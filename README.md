# Examen Segundo Parcial — Pipeline de datos contenerizado

Matrícula: **125054263**. El último dígito es **3**, por lo que la pregunta asignada es el **ticket promedio (cantidad × precio_unitario) por tienda**.

## Preparación y arranque

Requiere Docker Desktop con Compose v2 y Python 3. El CSV es local y está excluido de Git.

```powershell
python generar_dataset.py 125054263
New-Item -ItemType Directory -Force data/input | Out-Null
Copy-Item -Force ventas_125054263.csv data/input/
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

La generación del CSV se hace una vez antes de iniciar los servicios. Después, `docker compose up --build` construye y levanta Hadoop, PostgreSQL y la API; el servicio `job` ejecuta Hadoop Streaming y termina, y la API espera a que el job finalice y carga `part-00000` a PostgreSQL. El dataset se monta como volumen de solo lectura para no inflar la imagen ni reconstruirla al cambiarlo.

Para volver a iniciar los servicios ya construidos, usa `docker compose up -d`. Para ejecutar manualmente solo el procesamiento y refrescar la tabla: `docker compose run --rm job` y luego `docker compose restart api`.

## Comprobaciones de infraestructura

```powershell
docker compose exec hadoop hadoop version
docker compose exec hadoop bash -lc "su - hadoop -c 'ssh -o BatchMode=yes -o LogLevel=ERROR localhost echo SSH_LOCALHOST_OK'"
docker compose exec api sh -c "ssh -o BatchMode=yes -o LogLevel=ERROR hadoop@hadoop 'echo SSH_API_TO_HADOOP_OK'"
docker compose logs job
```

Hadoop trabaja en modo standalone/local: Streaming ejecuta el job sin HDFS. El resultado queda en `data/output/resultado/part-00000`.

## API y persistencia

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/resultados
Invoke-RestMethod http://localhost:8000/resultados/T001
Invoke-RestMethod -Method Post -Uri http://localhost:8000/resultados -ContentType 'application/json' -Body '{"clave":"T999","ticket_promedio":100.5,"registros":2}'
docker compose down
docker compose up -d
Invoke-RestMethod http://localhost:8000/resultados
```

La carga y el POST usan `ON CONFLICT`, por lo que se pueden repetir. `docker compose down` conserva el volumen nombrado `postgres-data`; `docker compose down -v` también lo borra y obliga a reconstruir/reiniciar el pipeline para recuperar los datos.

## Comparativa de rendimiento

```powershell
$secuencial = Measure-Command { python mapreduce/secuencial.py data/input/ventas_125054263.csv > evidencias/secuencial.tsv }
$secuencial.TotalSeconds
python scripts/comparar_resultados.py evidencias/secuencial.tsv data/output/resultado/part-00000
```

El tiempo Hadoop queda en `docker compose logs job` (incluye la medición `time` del job). El comparador verifica tienda, promedio con dos decimales y cantidad de registros. En este escenario el script secuencial suele ser más rápido porque evita arrancar la JVM y pagar el coste de serialización y coordinación de Hadoop; MapReduce conviene al crecer el volumen, al distribuir el trabajo entre nodos o cuando se necesita tolerancia a fallos.

Mediciones de esta entrega: secuencial **26.71 s** y Hadoop **102.71 s** para 5,000,000 de registros y 25 tiendas. Hadoop tuvo coste de inicio y coordinación en modo local. La salida y el conteo coinciden; ver `evidencias/secuencial-tiempo.txt`, `evidencias/job.txt` y `evidencias/comparacion.txt`.

## Teoría

### 1. Modos de Hadoop y HDFS

En modo **standalone**, Hadoop ejecuta MapReduce localmente y no inicia daemons ni usa HDFS; este proyecto corre así.
En modo **pseudo-distribuido**, los daemons se ejecutan en una sola máquina y Hadoop guarda los archivos en HDFS.
En modo **totalmente distribuido**, los daemons se reparten entre varias máquinas y HDFS distribuye los bloques entre nodos.
Por tanto, HDFS se usa en pseudo-distribuido y totalmente distribuido, pero no es necesario para el job local de este examen.

### 2. Montar el CSV como volumen

El CSV ocupa cientos de megabytes; copiarlo a la imagen la haría más grande y lenta de construir.
Como volumen se puede reemplazar el dataset sin reconstruir la imagen.
Además, el archivo puede excluirse de Git y montarse en `/data/input` como solo lectura para protegerlo durante el job.

### 3. `docker compose down` y `down -v`

`docker compose down` detiene y elimina contenedores y la red del proyecto.
Los volúmenes nombrados permanecen, así que PostgreSQL conserva la tabla y sus resultados al volver a iniciar.
`docker compose down -v` también elimina esos volúmenes y borra los datos de la base.
Después de `down -v`, el job y la API vuelven a cargar la tabla al levantar el pipeline.

### 4. Rendimiento de MapReduce

MapReduce paga el costo de iniciar la JVM, dividir el archivo, serializar datos y coordinar las tareas.
Con un CSV de 400 MB y una sola máquina, un script secuencial evita esos costos y puede ser más rápido.
En esta ejecución, el secuencial tardó 26.71 s y Hadoop 102.71 s; ambos produjeron los mismos resultados.
MapReduce conviene cuando hay mucho más volumen, varios nodos para paralelizar o se necesita tolerancia a fallos.

### 5. `CMD`/`ENTRYPOINT` y `COPY`/`ADD`

`ENTRYPOINT` define el programa principal del contenedor; `CMD` define argumentos predeterminados y se puede reemplazar al iniciar el contenedor.
Por ejemplo, Hadoop usa un `ENTRYPOINT` para inicializar SSH; el servicio `job` lo reemplaza para ejecutar el script de procesamiento.
`COPY` copia archivos de forma directa; `ADD` también tiene funciones adicionales como extraer ciertos archivos tar.
Se prefiere `COPY` cuando solo se necesita copiar, porque deja explícito qué hace la instrucción.

## Preparación para la defensa oral

- **Cambiar el puerto de la API:** modifica `API_PORT` en `.env` (por ejemplo, `8001`) y recrea la API con `docker compose up -d --force-recreate api`. La aplicación sigue escuchando en el puerto interno 8000; Compose cambia el puerto del host.
- **Explicar el MapReduce:** el mapper lee cada venta y emite `tienda`, `cantidad × precio_unitario` y `1`. Hadoop agrupa por tienda; el reducer suma el ingreso y el conteo, y calcula `ingreso total / registros`.
- **Filtrar por mes:** la columna `fecha_hora` es `row[1]`; el mapper puede analizarla y descartar ventas fuera del mes elegido antes de emitir la clave. Si cambia la clave de agrupación, el reducer debe agrupar con esa nueva clave también.
- **Borrar y recargar la base:** `docker compose down -v` elimina el volumen de PostgreSQL. Al ejecutar `docker compose up --build`, el job genera la salida y la API vuelve a cargar los resultados; esta acción borra los datos persistidos anteriores.
- **Diagnosticar el arranque:** revisa `docker compose ps -a` y `docker compose logs job api db`. La API espera a que PostgreSQL esté saludable y a que el job termine correctamente; si falta el CSV, el job informa la ruta esperada y falla antes de iniciar la API.

## Evidencias

Después de levantar correctamente los servicios y generar `evidencias/secuencial.tsv`, ejecuta `./scripts/capturar_evidencias.ps1` desde PowerShell. El script guarda las salidas de `hadoop version`, ambos accesos SSH, logs del job, respuesta de `/resultados`, comparación y persistencia después de `down`/`up`. No guardes el CSV ni `.env` en el repositorio.
