package dev.portfoliolab.api.jobs;

import liquibase.Liquibase;
import liquibase.database.Database;
import liquibase.database.DatabaseFactory;
import liquibase.database.OfflineConnection;
import liquibase.resource.ClassLoaderResourceAccessor;
import org.junit.jupiter.api.Test;

class LiquibaseChangeLogTest {
    @Test
    void changelogParsesForPostgresql() throws Exception {
        var resources = new ClassLoaderResourceAccessor();
        Database database = DatabaseFactory.getInstance().findCorrectDatabaseImplementation(
                new OfflineConnection("offline:postgresql", resources));
        new Liquibase("db/changelog/db.changelog-master.yaml", resources, database).validate();
    }
}
