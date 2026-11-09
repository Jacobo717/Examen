$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$dir = Join-Path $root "evidencias"
New-Item -ItemType Directory -Force $dir | Out-Null

function Wait-ForApi {
    param([int]$TimeoutSeconds = 600)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            Invoke-RestMethod http://localhost:8000/health | Out-Null
            return
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)
    throw "La API no estuvo disponible en $TimeoutSeconds segundos. Revisa docker compose logs."
}

docker compose up -d 2>&1 | Tee-Object (Join-Path $dir "compose-up.txt")
Wait-ForApi
docker compose exec hadoop hadoop version 2>&1 | Tee-Object (Join-Path $dir "hadoop-version.txt")
docker compose exec hadoop bash -lc "su - hadoop -c 'ssh -o BatchMode=yes -o LogLevel=ERROR localhost echo SSH_LOCALHOST_OK'" 2>&1 | Tee-Object (Join-Path $dir "ssh-localhost.txt")
docker compose exec api sh -c "ssh -o BatchMode=yes -o LogLevel=ERROR hadoop@hadoop 'echo SSH_API_TO_HADOOP_OK'" 2>&1 | Tee-Object (Join-Path $dir "ssh-api-hadoop.txt")
Invoke-RestMethod http://localhost:8000/resultados |
    ConvertTo-Json -Depth 4 |
    Set-Content -Encoding utf8 (Join-Path $dir "api-resultados.json")
Invoke-RestMethod http://localhost:8000/resultados/T001 |
    ConvertTo-Json -Depth 4 |
    Set-Content -Encoding utf8 (Join-Path $dir "api-tienda-T001.json")
$payload = @{ clave = "T999"; ticket_promedio = 100.5; registros = 2 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/resultados -ContentType "application/json" -Body $payload |
    ConvertTo-Json -Depth 4 |
    Set-Content -Encoding utf8 (Join-Path $dir "api-post.json")
Invoke-RestMethod -Method Delete -Uri http://localhost:8000/resultados/T999 | Out-Null
python scripts/comparar_resultados.py evidencias/secuencial.tsv data/output/resultado/part-00000 2>&1 |
    Tee-Object (Join-Path $dir "comparacion.txt")

$persistencia = Join-Path $dir "persistencia.txt"
"ANTES DE down: $(Get-Date -Format o)" | Set-Content -Encoding utf8 $persistencia
docker compose down 2>&1 | Add-Content -Encoding utf8 $persistencia
docker compose up -d 2>&1 | Add-Content -Encoding utf8 $persistencia
Wait-ForApi
Invoke-RestMethod http://localhost:8000/resultados |
    ConvertTo-Json -Depth 4 |
    Add-Content -Encoding utf8 $persistencia
"Persistencia verificada: $(Get-Date -Format o)" | Add-Content -Encoding utf8 $persistencia
docker compose logs --no-color job 2>&1 | Tee-Object (Join-Path $dir "job.txt")
