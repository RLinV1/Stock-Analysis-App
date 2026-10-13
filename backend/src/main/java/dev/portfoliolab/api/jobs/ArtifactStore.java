package dev.portfoliolab.api.jobs;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import software.amazon.awssdk.core.exception.SdkException;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;

/** Reads worker-registered artifacts; never trusts object bytes without the database hash. */
@Component
public class ArtifactStore {
    static final int MAX_MANIFEST_BYTES = 1024 * 1024;
    private final S3Client s3;
    private final String bucket;

    @Autowired
    public ArtifactStore(@Value("${ARTIFACT_BUCKET:portfolio-lab-artifacts}") String bucket,
                         @Value("${S3_ENDPOINT_URL:}") String endpoint,
                         @Value("${AWS_REGION:us-east-1}") String region) {
        this(client(endpoint, region), bucket);
    }

    public ArtifactStore(S3Client s3, String bucket) {
        this.s3 = s3;
        this.bucket = bucket;
    }

    /** Raised when an object is missing, unreadable, oversized or fails its registered hash. */
    public static final class ArtifactUnavailable extends RuntimeException {
        private final String code;

        public ArtifactUnavailable(String code, Throwable cause) {
            super(code, cause);
            this.code = code;
        }

        public String code() {
            return code;
        }
    }

    public byte[] readVerified(String key, String expectedSha256) {
        final byte[] content;
        try (InputStream body = s3.getObject(GetObjectRequest.builder().bucket(bucket).key(key).build())) {
            content = body.readNBytes(MAX_MANIFEST_BYTES + 1);
        } catch (SdkException | IOException ex) {
            throw new ArtifactUnavailable("artifact_unavailable", ex);
        }
        if (content.length > MAX_MANIFEST_BYTES) {
            throw new ArtifactUnavailable("artifact_too_large", null);
        }
        if (!sha256(content).equals(expectedSha256)) {
            throw new ArtifactUnavailable("artifact_integrity_failure", null);
        }
        return content;
    }

    private static S3Client client(String endpoint, String region) {
        var builder = S3Client.builder().region(Region.of(region))
                .forcePathStyle(true);
        if (!endpoint.isBlank()) {
            builder.endpointOverride(URI.create(endpoint));
        }
        return builder.build();
    }

    private static String sha256(byte[] content) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content));
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException("SHA-256 is unavailable", ex);
        }
    }
}
