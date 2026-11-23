# Cutoff Check

Prueba local para saber si un dato o una revisión declarada llegaron antes del instante en que un modelo tomó una decisión. Ordenar el dataset por fecha no basta: el cierre del trimestre no es la fecha de publicación de sus cifras.

```sh
python3 cutoff_check.py examples/mixed.csv
python3 -m unittest discover -s tests -v
```

El ejemplo es sintético: una fila llega a tiempo y otra un minuto tarde. La salida es JSON; código 0 si pasa, 1 si detecta uso anticipado y 2 si la entrada es inválida. El programa no verifica la procedencia ni la veracidad de los timestamps, no elige vintages y no certifica un backtest. Consulta el [contrato CSV](README.md) antes de integrarlo.
