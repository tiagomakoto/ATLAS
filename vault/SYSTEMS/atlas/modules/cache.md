---
uid: mod-atlas-033
version: 1.0
status: validated
owner: Chan
function: Cache LRU assíncrono com TTL e eviction por tamanho — provê instância singleton analytics_cache para dados de analytics.
file: atlas_backend/core/cache.py
role: Camada de cache — evita recomputação de analytics pesados entre requests.
input:
  - key: str — chave de cache
  - value: Any — valor a armazenar
output:
  - get: Optional[Any] — valor cacheado se dentro do TTL, else None
  - analytics_cache: LRUCache — singleton (max_size=50, ttl=60s)
depends_on: []
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
intent:
  - Evitar recomputação de walk-forward, distribuição, ACF e tail metrics a cada request de analytics.
constraints:
  - LRUCache: max_size=128 default, ttl=60s default
  - analytics_cache singleton: max_size=50, ttl=60s
  - asyncio.Lock para concorrência
  - TTL lazy — expirado na leitura, não ativamente
  - Eviction LRU quando max_size excedido
notes:
  - analytics_cache é o único consumidor atual — outros caches podem ser criados conforme necessidade
