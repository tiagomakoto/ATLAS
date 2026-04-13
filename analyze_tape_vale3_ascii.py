from delta_chaos.tape import tape_historico_carregar
import pandas as pd

anos = list(range(2024, 2027))
df = tape_historico_carregar(ativos=["VALE3"], anos=anos, forcar=False)
df_vale = df[df["ativo_base"] == "VALE3"].copy()
df_vale["mes"] = pd.to_datetime(df_vale["data"]).dt.to_period("M")
resumo = df_vale.groupby("mes")["data"].count()
print("Registros TAPE VALE3 por mês 2024–2026:")
print(resumo.to_string())