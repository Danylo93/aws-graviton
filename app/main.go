package main

import (
    "encoding/json"
    "log"
    "net/http"
    "os"
    "runtime"
    "time"
)

func handler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    _ = json.NewEncoder(w).Encode(map[string]string{
        "message": "Olá, AWS Graviton!", "architecture": runtime.GOARCH,
        "version": os.Getenv("APP_VERSION"), "time": time.Now().UTC().Format(time.RFC3339),
    })
}

func routes() http.Handler {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /", handler)
    mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        _, _ = w.Write([]byte(`{"status":"ok"}`))
    })
    return mux
}

func main() {
    server := &http.Server{Addr: ":8080", Handler: routes(), ReadHeaderTimeout: 5 * time.Second}
    log.Fatal(server.ListenAndServe())
}
