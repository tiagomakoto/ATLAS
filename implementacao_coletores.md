# Implementação dos Coletores de Dados

Vou implementar os coletores de dados conforme especificado na v1. Os coletores serão implementados na seguinte ordem:

1. preco_volume.py - Coleta dados de preço e volume de ativos
2. macro_brasil.py - Coleta dados macroeconômicos do Brasil
3. macro_global.py - Coleta dados macroeconômicos globais
4. alternativo.py - Coleta dados alternativos (Google Trends, ANEEL, etc.)
5. noticias.py - Coleta e analisa notícias para calcular temperatura

Cada coletor seguirá a interface obrigatória especificada:
- Função `coletar(tickers: list[str] | None = None) -> int`
- Retorna número de registros inseridos
- Nunca lança exceção para o caller
- Append-only: nunca faz UPDATE em registros existentes
- Usa INSERT OR IGNORE para evitar duplicatas