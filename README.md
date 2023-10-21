# tournament-service-backend

to create local database
```bash
docker compose up postgres -d
# wait for a bit
docker ps --format "{{.ID}}: {{.Names}}" | grep "foosball-tournament-backend-postgres" | cut -d: -f 1 | xargs -I {} docker exec {} bash -c "su - postgres -c \"createdb foosball\"" && echo database created
```
