package dev.portfoliolab.api.jobs;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Map;

import dev.portfoliolab.api.jobs.ArtifactStore.ArtifactUnavailable;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.core.env.MapPropertySource;
import software.amazon.awssdk.core.ResponseInputStream;
import software.amazon.awssdk.http.AbortableInputStream;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectResponse;
import software.amazon.awssdk.services.s3.model.NoSuchKeyException;

class ArtifactStoreTest {
    private static final byte[] INDEX = "{\"files\":[]}".getBytes(StandardCharsets.UTF_8);

    @Test
    void returnsBytesMatchingRegisteredHash() throws Exception {
        FakeS3 s3 = new FakeS3(INDEX);
        byte[] read = new ArtifactStore(s3, "lab").readVerified("runs/a/index.json", sha256(INDEX));
        assertArrayEquals(INDEX, read);
        assertEquals("lab", s3.request.bucket());
        assertEquals("runs/a/index.json", s3.request.key());
    }

    @Test
    void rejectsTamperedObject() throws Exception {
        String registered = sha256(INDEX);
        var store = new ArtifactStore(new FakeS3("{\"files\":[1]}".getBytes(StandardCharsets.UTF_8)), "lab");
        var failure = assertThrows(ArtifactUnavailable.class, () -> store.readVerified("k", registered));
        assertEquals("artifact_integrity_failure", failure.code());
    }

    @Test
    void rejectsOversizedObject() {
        var store = new ArtifactStore(new FakeS3(new byte[ArtifactStore.MAX_MANIFEST_BYTES + 1]), "lab");
        var failure = assertThrows(ArtifactUnavailable.class, () -> store.readVerified("k", "0".repeat(64)));
        assertEquals("artifact_too_large", failure.code());
    }

    @Test
    void mapsMissingObjectToStableCode() {
        var store = new ArtifactStore(new FakeS3(null), "lab");
        var failure = assertThrows(ArtifactUnavailable.class, () -> store.readVerified("k", "0".repeat(64)));
        assertEquals("artifact_unavailable", failure.code());
    }

    @Test
    void springWiresConfiguredStoreWithoutContactingStorage() {
        try (var context = new AnnotationConfigApplicationContext()) {
            context.getEnvironment().getPropertySources().addFirst(new MapPropertySource("test",
                    Map.of("S3_ENDPOINT_URL", "http://localstack:4566", "ARTIFACT_BUCKET", "lab")));
            context.register(ArtifactStore.class);
            context.refresh();
            assertNotNull(context.getBean(ArtifactStore.class));
        }
    }

    private static String sha256(byte[] content) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content));
    }

    private static final class FakeS3 implements S3Client {
        private final byte[] content;
        private GetObjectRequest request;

        private FakeS3(byte[] content) {
            this.content = content;
        }

        @Override
        public ResponseInputStream<GetObjectResponse> getObject(GetObjectRequest getObjectRequest) {
            request = getObjectRequest;
            if (content == null) {
                throw NoSuchKeyException.builder().message("missing").build();
            }
            return new ResponseInputStream<>(GetObjectResponse.builder().build(),
                    AbortableInputStream.create(new ByteArrayInputStream(content)));
        }

        @Override
        public String serviceName() {
            return "s3";
        }

        @Override
        public void close() {}
    }
}
