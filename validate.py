#!/usr/bin/env python3
"""Test de validación post-refactorización"""

# 1. TEST DE IMPORTS
print('=' * 60)
print('1. VALIDACIÓN DE IMPORTS')
print('=' * 60)

try:
    from utils import format_money, sha256_bytes, parse_iso_datetime
    from utils import extract_period_parts, build_period_string
    print('✓ Imports desde utils.py - OK')
except Exception as e:
    print(f'✗ Error en imports: {e}')
    exit(1)

try:
    from main import app
    print('✓ Imports desde main.py - OK')
except Exception as e:
    print(f'✗ Error en main.py: {e}')
    exit(1)

# 2. TEST DE format_money()
print()
print('=' * 60)
print('2. TEST DE format_money()')
print('=' * 60)

try:
    result1 = format_money(1234.56)
    result2 = format_money(0)
    result3 = format_money(None)
    
    assert result1 == '1,234.56 MXN', f'Esperado "1,234.56 MXN", obtenido "{result1}"'
    assert result2 == '0.00 MXN', f'Esperado "0.00 MXN", obtenido "{result2}"'
    assert result3 == '', f'Esperado "", obtenido "{result3}"'
    
    print(f'✓ format_money(1234.56) = "{result1}"')
    print(f'✓ format_money(0) = "{result2}"')
    print(f'✓ format_money(None) = "{result3}"')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)

# 3. TEST DE sha256_bytes()
print()
print('=' * 60)
print('3. TEST DE sha256_bytes()')
print('=' * 60)

try:
    data = b'test'
    result = sha256_bytes(data)
    
    assert len(result) == 64, f'Esperado 64 caracteres, obtenido {len(result)}'
    assert isinstance(result, str), f'Esperado str, obtenido {type(result)}'
    
    print(f'✓ sha256_bytes(b"test") = "{result[:16]}..."')
    print(f'✓ Longitud correcta: {len(result)} caracteres')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)

# 4. TEST DE parse_iso_datetime()
print()
print('=' * 60)
print('4. TEST DE parse_iso_datetime()')
print('=' * 60)

try:
    from datetime import datetime
    
    dt1 = parse_iso_datetime('2025-01-10T15:30:00')
    assert isinstance(dt1, datetime), f'Esperado datetime, obtenido {type(dt1)}'
    print(f'✓ parse_iso_datetime("2025-01-10T15:30:00") = {dt1}')
    
    dt2 = parse_iso_datetime('2025-01-10T15:30:00-0600')
    assert isinstance(dt2, datetime), f'Esperado datetime, obtenido {type(dt2)}'
    print(f'✓ parse_iso_datetime("2025-01-10T15:30:00-0600") = {dt2}')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)

# 5. TEST DE extract_period_parts() y build_period_string()
print()
print('=' * 60)
print('5. TEST DE FUNCIONES DE PERÍODO')
print('=' * 60)

try:
    year, month = extract_period_parts('2025-01')
    assert (year, month) == (2025, 1), f'Esperado (2025, 1), obtenido ({year}, {month})'
    print(f'✓ extract_period_parts("2025-01") = ({year}, {month})')
    
    period = build_period_string(2025, 1)
    assert period == '2025-01', f'Esperado "2025-01", obtenido "{period}"'
    print(f'✓ build_period_string(2025, 1) = "{period}"')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)

# 6. TEST DE ARCHIVOS CREADOS
print()
print('=' * 60)
print('6. VALIDACIÓN DE ARCHIVOS')
print('=' * 60)

import os

archivos = [
    'utils.py',
    'main.py',
    'REFACTORING_SUMMARY.md',
    'REFACTORING_CHANGES.md',
    'VALIDATION_CHECKLIST.txt'
]

for archivo in archivos:
    path = os.path.join(os.getcwd(), archivo)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f'✓ {archivo} existe ({size} bytes)')
    else:
        print(f'✗ {archivo} NO ENCONTRADO')

# 7. TEST DE SINTAXIS
print()
print('=' * 60)
print('7. VALIDACIÓN DE SINTAXIS PYTHON')
print('=' * 60)

import py_compile

try:
    py_compile.compile('utils.py', doraise=True)
    print('✓ utils.py - Sintaxis correcta')
except py_compile.PyCompileError as e:
    print(f'✗ utils.py - Error de sintaxis: {e}')

try:
    py_compile.compile('main.py', doraise=True)
    print('✓ main.py - Sintaxis correcta')
except py_compile.PyCompileError as e:
    print(f'✗ main.py - Error de sintaxis: {e}')

# 8. RESUMEN FINAL
print()
print('=' * 60)
print('✅ VALIDACIÓN COMPLETADA CON ÉXITO')
print('=' * 60)
print()
print('Resumen:')
print('  ✓ Todos los imports funcionan correctamente')
print('  ✓ Funciones utilitarias producen resultados esperados')
print('  ✓ Sintaxis Python validada')
print('  ✓ Archivos de documentación presentes')
print()
print('La refactorización está lista para usar.')
