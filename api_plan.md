# Estrutura de Endpoints para API REST do Data Layer

## 1. Estrutura de Endpoints

### Tabela PRECO_VOLUME
- `GET /preco_volume/` - Listar todos os registros
- `GET /preco_volume/{ticker}` - Obter registros por ticker
- `GET /preco_volume/{ticker}/{data}` - Obter registro específico por ticker e data
- `POST /preco_volume/` - Criar novo registro
- `PUT /preco_volume/{ticker}/{data}` - Atualizar registro específico
- `DELETE /preco_volume/{ticker}/{data}` - Deletar registro específico

### Tabela FUNDAMENTALS
- `GET /fundamentals/` - Listar todos os registros
- `GET /fundamentals/{ticker}` - Obter registros por ticker
- `GET /fundamentals/{ticker}/{data_referencia}` - Obter registro específico
- `POST /fundamentals/` - Criar novo registro
- `PUT /fundamentals/{ticker}/{data_referencia}` - Atualizar registro
- `DELETE /fundamentals/{ticker}/{data_referencia}` - Deletar registro

### Tabela INDICADORES_COMPARTILHADOS
- `GET /indicadores_compartilhados/` - Listar todos os registros
- `GET /indicadores_compartilhados/{ticker}` - Obter por ticker
- `GET /indicadores_compartilhados/{ticker}/{data}` - Obter registro específico
- `POST /indicadores_compartilhados/` - Criar novo registro
- `PUT /indicadores_compartilhados/{ticker}/{data}` - Atualizar registro
- `DELETE /indicadores_compartilhados/{ticker}/{data}` - Deletar registro

### Tabela PORTFOLIO_ESTADO
- `GET /portfolio_estado/` - Listar todos os registros
- `GET /portfolio_estado/{id_posicao}` - Obter por ID
- `POST /portfolio_estado/` - Criar novo registro
- `PUT /portfolio_estado/{id_posicao}` - Atualizar registro
- `DELETE /portfolio_estado/{id_posicao}` - Deletar registro

### Tabela RETORNOS_HISTORICOS
- `GET /retornos_historicos/` - Listar todos os registros
- `GET /retornos_historicos/{ticker}` - Obter por ticker
- `POST /retornos_historicos/` - Criar novo registro
- `PUT /retornos_historicos/{ticker}` - Atualizar registro
- `DELETE /retornos_historicos/{ticker}` - Deletar registro

### Tabela TAXA_CONVERSAO
- `GET /taxa_conversao/` - Listar todos os registros
- `GET /taxa_conversao/{ticker}` - Obter por ticker
- `GET /taxa_conversao/{ticker}/{data_avaliacao}` - Obter registro específico
- `POST /taxa_conversao/` - Criar novo registro
- `PUT /taxa_conversao/{ticker}/{data_avaliacao}` - Atualizar registro
- `DELETE /taxa_conversao/{ticker}/{data_avaliacao}` - Deletar registro

### Tabela CICLO_GLOBAL
- `GET /ciclo_global/` - Listar todos os registros
- `GET /ciclo_global/{data}` - Obter por data
- `POST /ciclo_global/` - Criar novo registro
- `PUT /ciclo_global/{data}` - Atualizar registro
- `DELETE /ciclo_global/{data}` - Deletar registro

### Tabela CICLO_LOCAL_BRASIL
- `GET /ciclo_local_brasil/` - Listar todos os registros
- `GET /ciclo_local_brasil/{data}` - Obter por data
- `POST /ciclo_local_brasil/` - Criar novo registro
- `PUT /ciclo_local_brasil/{data}` - Atualizar registro
- `DELETE /ciclo_local_brasil/{data}` - Deletar registro

### Tabela FLUXO_INVESTIDORES
- `GET /fluxo_investidores/` - Listar todos os registros
- `GET /fluxo_investidores/{data}` - Obter por data
- `POST /fluxo_investidores/` - Criar novo registro
- `PUT /fluxo_investidores/{data}` - Atualizar registro
- `DELETE /fluxo_investidores/{data}` - Deletar registro

### Tabela FOCUS_BCB
- `GET /focus_bcb/` - Listar todos os registros
- `GET /focus_bcb/{data}` - Obter por data
- `POST /focus_bcb/` - Criar novo registro
- `PUT /focus_bcb/{data}` - Atualizar registro
- `DELETE /focus_bcb/{data}` - Deletar registro

### Outras tabelas
As mesmas operações CRUD (Create, Read, Update, Delete) devem ser implementadas para todas as outras tabelas do schema.

## 2. Modelos de Dados (Pydantic)

Cada tabela do schema terá seu modelo Pydantic correspondente. Exemplos:

```python
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class PrecoVolume(BaseModel):
    ticker: str
    data: date
    abertura: float
    maxima: float
    minima: float
    fechamento: float
    fechamento_adj: float
    volume: int
    fonte: str
    data_coleta: datetime
    flag_qualidade: bool

class Fundamentals(BaseModel):
    ticker: str
    data_referencia: date
    periodo: str
    receita_liquida: Optional[float]
    lucro_liquido: Optional[float]
    margem_liquida: Optional[float]
    roe: Optional[float]
    divida_liquida: Optional[float]
    ebitda: Optional[float]
    earnings_surprise: Optional[float]
    fonte: str
    data_coleta: datetime
```

## 3. Rotas e Controladores

A estrutura de rotas seguirá o padrão REST:
- `GET /api/v1/tabela/` - Listar todos os registros
- `GET /api/v1/tabela/{id}` - Obter registro específico
- `POST /api/v1/tabela/` - Criar novo registro
- `PUT /api/v1/tabela/{id}` - Atualizar registro
- `DELETE /api/v1/tabela/{id}` - Deletar registro

## 4. Autenticação e Segurança

- Implementar autenticação JWT
- Usar OAuth2 com escopos apropriados
- Validar tokens em todas as requisições
- Usar middlewares de segurança
- Criptografar senhas e tokens
- Implementar rate limiting
- Proteger endpoints com políticas de acesso apropriadas

Para concluir o plano, seguir as etapas abaixo:

1. Criar modelos Pydantic para cada tabela
2. Implementar rotas CRUD para cada tabela
3. Configurar autenticação e autorização
4. Adicionar middlewares de segurança
5. Implementar validações de dados
6. Adicionar testes automatizados
7. Documentar a API com Swagger/OpenAPI