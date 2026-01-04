job "embedding-service" {
  datacenters = ["dc1"]
  type = "service"

  group "embedding" {
    count = 1

    network {
      port "http" {
        static = 8001
        to = 8001
      }
    }

    task "embedding-service" {
      driver = "docker"

      config {
        image = "localhost:5000/embedding-service:latest"
      }

      env {
        PYTHONUNBUFFERED = "1"
      }

      resources {
        cpu = 500
        memory = 1024
      }

      logs {
        max_files = 3
        max_file_size = 10
      }
    }
  }
}
