# O binário é compilado fora da imagem para linux/arm64, estático.
FROM scratch
ARG COMMIT=local
LABEL org.opencontainers.image.revision=$COMMIT
COPY bin/server /server
EXPOSE 8080
USER 65532:65532
ENTRYPOINT ["/server"]
