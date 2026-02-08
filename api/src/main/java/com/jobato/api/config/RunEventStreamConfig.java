package com.jobato.api.config;

import com.jobato.api.messaging.RunEventsConsumer;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.stream.StreamMessageListenerContainer;

import java.time.Duration;

@Configuration
@ConditionalOnProperty(name = "jobato.redis.streams.enabled", havingValue = "true", matchIfMissing = true)
public class RunEventStreamConfig {
    private static final String STREAM_KEY = "ml:run-events";

    @Bean
    public StreamMessageListenerContainer<String, MapRecord<String, String, String>> runEventsStreamContainer(
        RedisConnectionFactory redisConnectionFactory,
        RunEventsConsumer runEventsConsumer
    ) {
        StreamMessageListenerContainer.StreamMessageListenerContainerOptions<String, MapRecord<String, String, String>> options =
            StreamMessageListenerContainer.StreamMessageListenerContainerOptions.builder()
                .pollTimeout(Duration.ofSeconds(1))
                .build();

        StreamMessageListenerContainer<String, MapRecord<String, String, String>> container =
            StreamMessageListenerContainer.create(redisConnectionFactory, options);
        container.receive(StreamOffset.create(STREAM_KEY, ReadOffset.from("0-0")), runEventsConsumer);
        container.start();
        return container;
    }
}
