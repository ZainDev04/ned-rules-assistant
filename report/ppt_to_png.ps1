param([string]$in, [string]$outdir)
$p = New-Object -ComObject PowerPoint.Application
$d = $p.Presentations.Open($in, $true, $false, $false)
New-Item -ItemType Directory -Force $outdir | Out-Null
$i = 1
foreach ($s in $d.Slides) { $s.Export((Join-Path $outdir ("s{0:D2}.png" -f $i)), "PNG", 1333, 750); $i++ }
$d.Close()
$p.Quit()
