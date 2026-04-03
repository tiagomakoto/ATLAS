import requests

url = "http://localhost:8000/delta-chaos/orchestrator/run"
headers = {"Content-Type": "application/json"}
data = {"source": "manual"}

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except requests.exceptions.ConnectionError:
    print("ERRO: Não foi possível conectar ao servidor em localhost:8000")
    print("Verifique se o backend está rodando.")
except Exception as e:
    print(f"ERRO: {e}")