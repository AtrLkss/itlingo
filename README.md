## Локальный запуск проекта

### Что нужно
- Python 3.11+
- pip
- Git
- Docker Desktop
- Windows + PowerShell

### 1. Клонировать проект
```powershell
git clone https://github.com/AtrLkss/itlingo/
cd itlingo
```
### 2. Создать виртуальное окружение
```powershell
python -m venv .venv
```
Если PowerShell не даёт запустить сккрипт:
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```
### 4. Установить зависимости
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```
### 5. Запустить Docker Desktop

### 6 Запустить проект
```powershell
python app.py
```
### 7 Открыть в браузере
```
http://127.0.0.1:5000
```
