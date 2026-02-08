FROM eclipse-temurin:17-jdk

WORKDIR /app

COPY . .
RUN apt-get update && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/*
RUN chmod +x ./gradlew

EXPOSE 8080

CMD ["./gradlew", "bootRun"]
