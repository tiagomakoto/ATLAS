# Análise Comparativa das Especificações do Data Layer

## Divergências Encontradas

Comparando a especificação v2 (anterior) com a v1 (atual), identifiquei as seguintes divergências que precisam ser ajustadas:

### 1. Arquitetura
- **Banco de dados**: v2 usava PostgreSQL, v1 usa SQLite
- **API**: v2 previa API REST, v1 não usa API REST
- **Orquestração**: v2 usava Airflow, v1 usa APScheduler

### 2. Componentes que mudaram
- **Scheduler**: De Airflow (v2) para APScheduler (v1)
- **Banco de dados**: De PostgreSQL (v2) para SQLite (v1)
- **Acesso ao banco**: De API REST (v2) para acesso direto via Python (v1)

### 3. Estrutura de pastas
A estrutura de pastas mudou significativamente entre as versões, com v1 usando uma estrutura específica diferente do v2.

### 4. Componentes principais
- `src/data_layer/db/` - Schema e conexão com o banco
- `src/data_layer/collectors/` - Coletores de dados
- `src/data_layer/scheduler.py` - Agendamento
- `src/data_layer/utils.py` - Funções utilitárias

### 5. Especificações técnicas
- Append-only: o histórico não deve ser alterado, apenas inserido
- Coletas diárias/noturnas de dados
- Coletores específicos para diferentes fontes de dados
- Validação de dados e logs estruturados

## Ajustes Necessários

1. **Remover implementação de API REST** - v1 não usa API REST
2. **Remover PostgreSQL** - v1 usa SQLite
3. **Remover Airflow** - v1 usa APScheduler
4. **Ajustar estrutura de pastas** para seguir o especificado na v1
5. **Implementar coletores conforme especificados** em `collectors/`
6. **Ajustar o acesso ao banco de dados** para SQLite e acesso direto
7. **Implementar o scheduler conforme especificado** no arquivo `scheduler.py`
8. **Validar dados conforme especificado** em `utils.py`

## Próximos passos
1. Criar estrutura de pastas conforme especificação
2. Implementar os módulos de banco de dados
3. Implementar coletores de dados
4. Implementar o scheduler
5. Ajustar utilitários
6. Validar implementação