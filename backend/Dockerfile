FROM maven:3.9.13-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY backend/pom.xml backend/pom.xml
COPY backend/src backend/src
COPY contracts contracts
RUN mvn -B -q -f backend/pom.xml package

FROM eclipse-temurin:21-jre-alpine-3.24
WORKDIR /app
COPY --from=build /workspace/backend/target/portfolio-lab-api-0.1.0-SNAPSHOT.jar app.jar
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
