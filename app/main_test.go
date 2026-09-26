package main

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "runtime"
    "testing"
)

func TestArchitectureAndHealth(t *testing.T) {
    for _, tc := range []struct{ path, key, want string }{
        {"/", "architecture", runtime.GOARCH}, {"/health", "status", "ok"},
    } {
        recorder := httptest.NewRecorder()
        routes().ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, tc.path, nil))
        if recorder.Code != http.StatusOK { t.Fatalf("%s: %d", tc.path, recorder.Code) }
        var got map[string]string
        if err := json.Unmarshal(recorder.Body.Bytes(), &got); err != nil { t.Fatal(err) }
        if got[tc.key] != tc.want { t.Fatalf("%s: %s=%q want %q", tc.path, tc.key, got[tc.key], tc.want) }
    }
}
