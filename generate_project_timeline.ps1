# PowerShell Script: Generate Project Timeline from Markdown Reports
# Descripción: Analiza todos los archivos .md en la raíz del proyecto
# y genera un informe cronológico consolidado

# Configuración
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputFile = Join-Path $projectRoot "PROJECT_TIMELINE_REPORT.txt"
$mdFiles = Get-ChildItem -Path $projectRoot -Filter "*.md" -File

Write-Host "🔍 Analizando archivos markdown del proyecto..." -ForegroundColor Cyan
Write-Host "📁 Directorio: $projectRoot`n" -ForegroundColor Gray

# Objeto para almacenar información de reportes
$reports = @()

# Buscar fechas en cada archivo .md
foreach ($file in $mdFiles) {
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    
    if ([string]::IsNullOrWhiteSpace($content)) { continue }
    
    # Patrones de fecha
    $datePatterns = @(
        '\*\*Fecha\*\*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',  # **Fecha**: 2025-12-13
        'Date[@:]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',         # Date: 2025-12-13
        '\[([0-9]{4}-[0-9]{2}-[0-9]{2})\]',                 # [2025-12-13]
        'Fecha[@:]?\s*([0-9]{1,2} de \w+ de [0-9]{4})'     # Fecha: 13 de diciembre de 2025
    )
    
    # Extraer fecha
    $foundDate = $null
    $dateObj = $null
    
    foreach ($pattern in $datePatterns) {
        if ($content -match $pattern) {
            $foundDate = $matches[1]
            # Intentar parsear como fecha ISO
            if ($foundDate -match '^\d{4}-\d{2}-\d{2}$') {
                try {
                    $dateObj = [datetime]::Parse($foundDate)
                }
                catch {
                    $dateObj = [datetime]::MaxValue
                }
                break
            }
        }
    }
    
    # Si no se encontró fecha ISO, usar fecha de modificación del archivo
    if ($null -eq $dateObj) {
        $dateObj = $file.LastWriteTime
        $foundDate = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    # Extraer descripción/contenido
    $lines = $content -split "\r?\n"
    $title = $file.BaseName
    $description = ""
    $status = "Unknown"
    $keyPoints = @()
    
    # Buscar título (primer heading)
    foreach ($line in $lines) {
        if ($line -match '^#+\s+(.+)$') {
            $title = $matches[1].Trim()
            break
        }
    }
    
    # Buscar estado
    foreach ($line in $lines) {
        if ($line -match 'Estado\s*[:=]\s*([^\r\n]+)' -or 
            $line -match 'Status\s*[:=]\s*([^\r\n]+)' -or
            $line -match 'ESTADO\s*[:=]\s*([^\r\n]+)') {
            $status = $matches[1].Trim()
            break
        }
    }
    
    # Buscar puntos clave (items con ✅, ❌, etc)
    foreach ($line in $lines) {
        if ($line -match '^[\s]*[-*]\s*[✅❌⏳⚠️❗]\s*(.+)$') {
            $keyPoints += "  • " + $matches[1].Trim()
        }
        elseif ($line -match '^[\s]*###\s+(.+)$') {
            $keyPoints += "  → " + $matches[1].Trim()
        }
    }
    
    # Tomar primeras líneas de descripción
    $descLines = @()
    foreach ($line in $lines) {
        if ($line -match '^#+\s+' -or [string]::IsNullOrWhiteSpace($line)) { continue }
        if ($descLines.Count -lt 3 -and $line.Length -gt 10) {
            $descLines += $line.Trim()
        }
    }
    $description = ($descLines -join " ").Substring(0, [Math]::Min(200, ($descLines -join " ").Length))
    
    # Agregar al arreglo de reportes
    $reportObj = @{
        Date       = $dateObj
        DateStr    = $foundDate
        FileName   = $file.Name
        Title      = $title
        Status     = $status
        Description = $description
        KeyPoints  = $keyPoints
        FileSize   = "{0:N0}" -f ($file.Length / 1KB) + " KB"
    }
    
    $reports += $reportObj
}

# Ordenar por fecha (descendente - más reciente primero)
$reports = $reports | Sort-Object -Property Date -Descending

# Generar informe
$report = @()
$report += "================================================================================="
$report += "                  PROJECT TIMELINE REPORT - SubjectsSupport"
$report += "                   Cronologia Consolidada de Cambios"
$report += "================================================================================="
$report += ""
$report += "RESUMEN EJECUTIVO"
$report += "================================================================================="
$report += "Total de reportes analizados: $($reports.Count)"
$report += "Rango temporal: $($reports[-1].DateStr) hasta $($reports[0].DateStr)"
$report += "Tamaño total: $($reports | Measure-Object -Property FileSize -Sum | Select -ExpandProperty Sum)"
$report += ""

# Tabla resumen cronológica
$report += "CRONOLOGIA DETALLADA (Mas Reciente -> Mas Antiguo)"
$report += "================================================================================="
$report += ""

$index = 1
foreach ($rep in $reports) {
    $report += "[$index] FECHA: $($rep.DateStr)"
    $report += "    Archivo: $($rep.FileName)"
    $report += "    Titulo: $($rep.Title)"
    $report += "    Estado: $($rep.Status)"
    $report += "    Tamano: $($rep.FileSize)"
    
    if ($rep.Description -and $rep.Description.Length -gt 0) {
        $report += "    Descripcion: $($rep.Description)..."
    }
    
    if ($rep.KeyPoints.Count -gt 0) {
        $report += "    Puntos Clave:"
        foreach ($point in $rep.KeyPoints | Select-Object -First 3) {
            $report += "       $point"
        }
        if ($rep.KeyPoints.Count -gt 3) {
            $report += "       ... y $($rep.KeyPoints.Count - 3) mas"
        }
    }
    
    $report += ""
    $index++
}

# Estadísticas por tipo
$report += "ESTADISTICAS DE REPORTES"
$report += "================================================================================="
$report += ""

$statusGroups = $reports | Group-Object -Property Status
foreach ($group in $statusGroups) {
    $report += "  [$($group.Count)] $($group.Name)"
}

$report += ""
$report += "ARCHIVOS ANALIZADOS (Orden Alfabetico)"
$report += "================================================================================="
$report += ""

foreach ($rep in ($reports | Sort-Object -Property FileName)) {
    $report += "  - $($rep.FileName)"
}

$report += ""
$report += "================================================================================="
$report += "Generado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$report += "================================================================================="

# Guardar informe
$report | Out-File -FilePath $outputFile -Encoding UTF8

Write-Host "✅ Informe generado exitosamente!" -ForegroundColor Green
Write-Host "📁 Ubicación: $outputFile" -ForegroundColor Cyan
Write-Host "📊 Total de reportes: $($reports.Count)" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Primeras líneas del informe:" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$report | Select-Object -First 30 | ForEach-Object { Write-Host $_ }
Write-Host ""
Write-Host "Abre $outputFile para ver el informe completo" -ForegroundColor Gray
