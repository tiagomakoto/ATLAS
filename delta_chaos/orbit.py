# ════════════════════════════════════════════════════════════════════
# DELTA CHAOS — ORBIT
# Alterações em relação à v3.4:
# MIGRADO (P2): imports explícitos de init e tape — sem escopo global
# MIGRADO (P5): prints de inicialização sob if __name__ == "__main__"
# MANTIDO: S1–S6, calibração Ridge, regimes, NEUTRO_LATERAL/MORTO
# ════════════════════════════════════════════════════════════════════

from delta_chaos.init import (
    carregar_config, ATIVOS_DIR, BOOK_DIR,
    OHLCV_DIR, EXTERNAS_DIR,
)
from delta_chaos.tape import (
    tape_ativo_carregar, tape_ciclo_salvar,
    tape_ohlcv_carregar, tape_ibov_carregar, tape_externa_carregar,
    tape_ciclo_para_data,
    _obter_selic,
)

# ── Logging ATLAS (graceful fallback) ─────────────────────────────────
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False

# ════════════════════════════════════════════════════════════════════
# DELTA CHAOS — ORBIT v3.5
# Alterações em relação à v3.3:
# CORRIGIDO (SCAN-10): removida importação morta de tape_reflect_cycle
#   tape_reflect_cycle é chamado pelo EDGE, não pelo ORBIT
# CORRIGIDO: pbar.set_postfix estava após continue — nunca executava
# MANTIDO: todo o restante idêntico à v3.3
# ════════════════════════════════════════════════════════════════════

import os, math, warnings
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from tqdm.auto import tqdm as _tqdm
warnings.filterwarnings("ignore")

# ── Parâmetros via config global ──────────────────────────────────
_cfg = carregar_config()["orbit"]

HORIZONTE_DIAS      = _cfg["horizonte_dias"]
PCT_TREINO          = _cfg["pct_treino"]
PERCENTIL_THRESHOLD = _cfg["percentil_threshold"]
RIDGE_LAMBDA        = _cfg["ridge_lambda"]
RECALIBRAR_DIAS     = _cfg["recalibrar_dias"]
JANELA_OLS          = _cfg["janela_ols"]
IR_OPERAR           = _cfg["ir_operar"]
IR_MONITORAR        = _cfg["ir_monitorar"]
LAMBDA_TEMPORAL     = _cfg["lambda_temporal"]
VEL_RECUPERACAO     = _cfg["vel_recuperacao"]
VEL_PANICO          = _cfg["vel_panico"]
VOL_PANICO          = _cfg["vol_panico"]
CICLOS_NEG_MIN      = _cfg["ciclos_neg_min"]

# SCAN-10: tape_reflect_cycle removido — é chamado pelo EDGE, não pelo ORBIT
# P2: imports explícitos abaixo (substituem escopo global do notebook)

# ════════════════════════════════════════════════════════════════════
# INDICADORES
# ════════════════════════════════════════════════════════════════════

def _calc_adx(h, l, c, p=14):
    n=len(c); tr=np.zeros(n); dmp=np.zeros(n); dmm=np.zeros(n)
    for i in range(1,n):
        tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
        u,d=h[i]-h[i-1],l[i-1]-l[i]
        dmp[i]=u if u>d and u>0 else 0
        dmm[i]=d if d>u and d>0 else 0
    def wld(x):
        o=np.zeros(len(x)); o[p]=np.sum(x[1:p+1])
        for i in range(p+1,len(x)): o[i]=o[i-1]-o[i-1]/p+x[i]
        return o
    atr=wld(tr); sp=wld(dmp); sm=wld(dmm)
    with np.errstate(divide='ignore',invalid='ignore'):
        dp=np.where(atr>0,100*sp/atr,0)
        dm=np.where(atr>0,100*sm/atr,0)
        dx=np.where((dp+dm)>0,100*np.abs(dp-dm)/(dp+dm),0)
    return wld(dx),dp,dm

def _calc_obv(c, v):
    o=np.zeros(len(c))
    for i in range(1,len(c)):
        o[i]=o[i-1]+(v[i] if c[i]>c[i-1] else
                     -v[i] if c[i]<c[i-1] else 0)
    return o

def _calc_cmf(h, l, c, v, p=20):
    hl=np.where((h-l)==0,1e-10,h-l)
    mfv=((2*c-h-l)/hl)*v
    return (pd.Series(mfv).rolling(p).sum()/
            pd.Series(v).rolling(p).sum()).values

def _calc_rsi(c, p=14):
    d=np.diff(c,prepend=c[0])
    ag=pd.Series(np.where(d>0,d,0)).ewm(
        com=p-1,adjust=False).mean().values
    al=pd.Series(np.where(d<0,-d,0)).ewm(
        com=p-1,adjust=False).mean().values
    return 100-100/(1+ag/np.where(al==0,1e-10,al))

def _calc_beta_rolling(ra, rb, p=21):
    a,b=pd.Series(ra),pd.Series(rb)
    return (a.rolling(p).cov(b)/
            b.rolling(p).var().replace(0,1e-10)).values

# ════════════════════════════════════════════════════════════════════
# CAMADAS
# ════════════════════════════════════════════════════════════════════

def _calcular_camadas(df, ib, externas_dict=None):
    c=df["close"].values if "close" in df.columns \
      else df["fechamento"].values
    h=df["high"].values  if "high"  in df.columns else c*1.005
    l=df["low"].values   if "low"   in df.columns else c*0.995
    v=df["volume"].values

    lr=np.log(pd.Series(c)/pd.Series(c).shift(1))
    v21=lr.rolling(21).std().values*math.sqrt(252)
    v63=lr.rolling(63).std().values*math.sqrt(252)
    vg =lr.ewm(span=21,adjust=False).std().values*math.sqrt(252)
    v21=np.nan_to_num(v21,nan=0.2)
    v63=np.nan_to_num(v63,nan=0.2)
    vg =np.nan_to_num(vg, nan=0.2)

    adx_a,dip_a,dim_a=_calc_adx(h,l,c)
    sma21 =pd.Series(c).rolling(21).mean().values
    sma50 =pd.Series(c).rolling(50).mean().values
    sma200=pd.Series(c).rolling(200).mean().values
    sl21  =pd.Series(sma21).diff(6).values/(sma21+1e-10)
    with np.errstate(invalid='ignore',divide='ignore'):
        sa=np.where(adx_a<15,0,
           np.clip((adx_a-15)/25,0,1)*
           np.where(dip_a>dim_a,1,-1))
        g200=np.where(sma200>0,(sma50-sma200)/sma200,0)
        g50 =np.where(sma50>0,(sma21-sma50)/sma50,0)
        sm  =(np.tanh(g200*30)*0.5+
              np.tanh(g50*40)*0.3+
              np.tanh(sl21*600)*0.2)
        s1  =np.clip(0.55*sa+0.45*sm,-1,1)

    r10=pd.Series(c).pct_change(10).values
    r21=pd.Series(c).pct_change(21).values
    r63=pd.Series(c).pct_change(63).values
    rsi=_calc_rsi(c)
    rp =np.where(rsi>75,-0.10,np.where(rsi<25,0.10,0.0))
    cc =np.abs(np.sign(r10)+np.sign(r21)+np.sign(r63))/3
    sr =(np.tanh(r10*12)*0.30+
         np.tanh(r21*9)*0.40+
         np.tanh(r63*6)*0.30)
    s2 =np.clip(sr*(0.7+0.3*cc)+rp,-1,1)

    obv=_calc_obv(c,v)
    on =obv/(np.max(np.abs(obv))+1e-10)
    osl=pd.Series(on).diff(10).rolling(5).mean().values/10
    cmf=_calc_cmf(h,l,c,v)
    rc =np.diff(c,prepend=c[0])
    uv =pd.Series(np.where(rc>0,v,0)).rolling(10).sum().values
    dv =pd.Series(np.where(rc<0,v,0)).rolling(10).sum().values
    vr =uv/np.where(dv==0,1e-10,dv)
    s3 =np.clip(
        np.tanh(osl*120)*0.45+
        np.tanh((vr-1)*2.5)*0.30+
        np.tanh(np.nan_to_num(cmf)*6)*0.25,-1,1)

    gt=pd.Series(vg).diff(10).values/10
    sk=v21-v63
    s4=np.clip(np.tanh(-gt*20)*0.55+
               np.tanh(-sk*15)*0.45,-1,1)

    ra=pd.Series(c).pct_change().values
    ri=pd.Series(ib).pct_change().values
    ba=_calc_beta_rolling(ra,ri)
    bt=pd.Series(ba).diff(10).values/10
    rib=pd.Series(ib).pct_change(21).values
    bc=np.clip(np.nan_to_num(ba),0,2)/2
    s5=np.clip(
        np.tanh(rib*8)*bc-
        np.where((bt<-0.05)&(rib>0),0.20,0.0),-1,1)

    res=pd.DataFrame(
        {"s1":s1,"s2":s2,"s3":s3,"s4":s4,"s5":s5},
        index=df.index)

    if externas_dict is not None and len(externas_dict) > 0:
        sinais_externos = []
        for nome_serie in sorted(externas_dict.keys()):
            serie = externas_dict.get(nome_serie)
            if serie is None or len(serie) == 0:
                continue
            serie_alinhada = serie.reindex(
                df.index, method='ffill')
            fx_vals = serie_alinhada.values
            n = min(len(ra), len(fx_vals))
            if n < 10: continue
            rfx  = pd.Series(fx_vals[:n]).pct_change().values
            bfx  = _calc_beta_rolling(ra[:n], rfx)
            rfx21= pd.Series(
                fx_vals[:n]).pct_change(21).values
            bcfx = np.clip(np.nan_to_num(bfx), 0, 3) / 3
            sinal = np.tanh(rfx21 * 8) * bcfx
            sinal = np.clip(sinal, -1, 1)
            sinal_completo = np.full(len(res), np.nan)
            sinal_completo[:len(sinal)] = sinal
            sinais_externos.append(sinal_completo)

        if len(sinais_externos) > 0:
            matriz = np.column_stack(sinais_externos)
            s6 = np.nanmean(matriz, axis=1)
            s6 = np.nan_to_num(s6, nan=0.0)
            res['s6'] = s6

    return res

# ════════════════════════════════════════════════════════════════════
# CALIBRAÇÃO
# ════════════════════════════════════════════════════════════════════

def _pesos_temporais(df_idx):
    if LAMBDA_TEMPORAL <= 0:
        return np.ones(len(df_idx))
    datas = pd.to_datetime(df_idx)
    ref   = datas.max()
    dias  = (ref - datas).days.values.astype(float)
    return np.exp(-LAMBDA_TEMPORAL * dias)

def _calibrar(cam_df, ret_fut, prior_dict,
              pct_treino=0.70, lam=0.10):
    # PATCH v3.5: s6 opcional - detecta colunas presentes
    colunas_validas = [f"s{i}" for i in range(1, 7)
                       if f"s{i}" in cam_df.columns]
    if not colunas_validas:
        return {}, 0.0

    df_j=cam_df[colunas_validas].copy()
    df_j["ret"]=ret_fut
    df_j=df_j.dropna(how="any")
    
    # PATCH: recalcula apÃ³s dropna - remove colunas sem dados suficientes
    colunas_validas = [c for c in colunas_validas
                       if c in df_j.columns and df_j[c].notna().sum() > 20]
    if not colunas_validas:
        return {}, 0.0
        
    n=len(df_j); n_tr=int(n*pct_treino)

    pr=np.array([1.0/len(colunas_validas)
                 for _ in colunas_validas])

    if n_tr < 60:
        return {c:float(p)
                for c,p in zip(colunas_validas,pr)}, 0.0

    df_tr=df_j.iloc[:n_tr]
    w=_pesos_temporais(df_tr.index)
    w=w/w.sum()*len(w)

    # PATCH: garante colunas existem em df_tr
    colunas_validas = [c for c in colunas_validas if c in df_tr.columns]
    X=df_tr[colunas_validas].values
    y=df_tr["ret"].values
    W=np.diag(w)
    XtWX=X.T@W@X + lam*np.eye(len(colunas_validas))
    XtWy=X.T@W@y + lam*pr
    try:
        coefs=np.linalg.solve(XtWX,XtWy)
    except Exception:
        coefs=pr.copy()

    coefs_pos=np.maximum(coefs,0)
    for i,c in enumerate(colunas_validas):
        _coef_min = carregar_config()["orbit"]["coef_minimo_camada"]
        if coefs_pos[i] < _coef_min: coefs_pos[i] = _coef_min
    soma=coefs_pos.sum()
    coefs_pos=coefs_pos/soma if soma>1e-10 else pr
    pesos={c:float(v)
           for c,v in zip(colunas_validas,coefs_pos)}

    df_val=df_j.iloc[n_tr:]
    if len(df_val) > 10:
        sv=sum(df_val[c]*pesos[c]
               for c in colunas_validas
               if c in df_val.columns)
        rv=df_val["ret"].values
        mk=np.abs(sv)>0.01
        rs=np.where(sv>0,rv,
           np.where(sv<0,-rv,0))[mk]
        ir=(np.mean(rs)/(np.std(rs)+1e-10)*
            math.sqrt(252/HORIZONTE_DIAS)
            if len(rs)>5 else 0.0)
    else:
        ir=0.0

    return pesos, ir

def _score_rolante(cam_df, ret_fut, prior_dict,
                   janela=504, recal=126, lam=0.10):
    # PATCH v3.5: nÃ£o fixa colunas - _calibrar decide por janela (s6 opcional)
    colunas_base = [f"s{i}" for i in range(1, 7)
                       if f"s{i}" in cam_df.columns]

    n      = len(cam_df)
    scores = pd.Series(np.nan, index=cam_df.index)
    pw     = None
    ir_ok  = 0.0
    ph     = []
    rs_oos = []

    for i in range(janela, n):
        if pw is None or (i-janela) % recal == 0:
            ini=max(0, i-janela)
            pw, _ = _calibrar(
                cam_df.iloc[ini:i],
                ret_fut.iloc[ini:i],
                prior_dict,
                PCT_TREINO, lam)

            if len(rs_oos) > 5:
                rs_arr = np.array(rs_oos)
                ir_ok  = float(
                    np.mean(rs_arr)/
                    (np.std(rs_arr)+1e-10)*
                    math.sqrt(252/HORIZONTE_DIAS))
            else:
                ir_ok = 0.0

            ph.append({
                "idx":   i,
                "pesos": pw.copy() if pw else {},
                "ir":    ir_ok})

        if pw:
            # PATCH v3.5: usa apenas pesos retornados por _calibrar (5 ou 6 features)
            s = sum(cam_df.get(c, pd.Series(0, index=cam_df.index)).iloc[i] * w
                  for c, w in pw.items())
            s=float(np.clip(s,-1,1))
            scores.iloc[i]=s

            ret_i=ret_fut.iloc[i]
            if not np.isnan(ret_i) and abs(s)>0.01:
                rs_oos.append(
                    float(ret_i) if s>0
                    else -float(ret_i))

    if len(rs_oos) > 5:
        rs_arr   = np.array(rs_oos)
        ir_final = float(
            np.mean(rs_arr)/
            (np.std(rs_arr)+1e-10)*
            math.sqrt(252/HORIZONTE_DIAS))
        if ph: ph[-1]["ir"] = ir_final

    return scores, ph

# ════════════════════════════════════════════════════════════════════
# REGIMES
# ════════════════════════════════════════════════════════════════════

def _classificar_regime(score_hist, vol_hist, thresh):
    if len(score_hist) < 3:
        s = score_hist[-1] if score_hist else 0
        if   s >  thresh: return "ALTA"
        elif s < -thresh: return "BAIXA"
        else:             return "NEUTRO"

    s_atual = score_hist[-1]
    s_ant1  = score_hist[-2]
    s_ant2  = score_hist[-3]
    score_vel = (s_atual - s_ant2) / 2

    vol_vel = 0.0
    if len(vol_hist) >= 2:
        vol_vel = vol_hist[-1] - vol_hist[-2]

    if (s_atual < -thresh and
        score_vel < -VEL_PANICO and
        vol_vel   >  VOL_PANICO):
        return "PANICO"

    ciclos_neg      = sum(
        1 for s in score_hist[-3:-1] if s < 0)
    vel_positiva_2c = (s_atual > s_ant1 > s_ant2)

    if (s_atual   <  0 and
        score_vel >  VEL_RECUPERACAO and
        ciclos_neg >= CICLOS_NEG_MIN and
        vel_positiva_2c):
        return "RECUPERACAO"

    if   s_atual >  thresh: return "ALTA"
    elif s_atual < -thresh: return "BAIXA"
    else:                   return "NEUTRO"

def _classificar_sub_regime_neutro(score, score_vel,
                                    vol_21d, vol_63d,
                                    thresh):
    abs_score = abs(score)
    abs_vel   = abs(score_vel)

    if abs_score > thresh * 0.85 and abs_vel > 0.05:
        return "NEUTRO_TRANSICAO"

    if abs_score < 0.05:
        if vol_21d > vol_63d:
            return "NEUTRO_LATERAL"
        else:
            return "NEUTRO_MORTO"

    if score > 0:
        return "NEUTRO_BULL"

    return "NEUTRO_BEAR"

# ════════════════════════════════════════════════════════════════════
# CLASSE ORBIT v3.5
# ════════════════════════════════════════════════════════════════════

class ORBIT:
    """
    ORBIT v3.5
    Dados via TAPE — sem acesso direto ao Drive
    Master JSON por ativo via tape_ativo_carregar / tape_ciclo_salvar
    tape_reflect_cycle removido — responsabilidade do EDGE
    """

    def __init__(self, universo: dict):
        self.universo = universo
        self.ativos   = list(universo.keys())
        print(f"  ORBIT v3.5 — {len(self.ativos)} ativos")
        print(f"  5 regimes | S6 unificada | dados via TAPE")

    def orbit_rodar(self, df_tape, anos, modo="pipeline", externas_dict=None, ciclos_forcados=None):
        df_cache, ciclos_faltantes = self.orbit_cache_carregar(anos)

        # Cache completo — retorna sem processar
        if not ciclos_faltantes:
            return df_cache

        ibov_close = tape_ibov_carregar(anos)
        if ibov_close.empty:
            print("  ✗ IBOV indisponível")
            return pd.DataFrame()

        ohlcv_ativos = {}
        for ativo in self.ativos:
            df_ohlcv = tape_ohlcv_carregar(ativo, anos)
            if not df_ohlcv.empty:
                ohlcv_ativos[ativo] = df_ohlcv
            else:
                print(f"  ⚠ {ativo} sem OHLCV — excluído")

        if not ohlcv_ativos:
            print("  ✗ Nenhum ativo com OHLCV")
            return pd.DataFrame()

        # Séries externas — recebidas do TAPE (não buscar internamente)
        self._externas_cache = externas_dict or {}

        # Aplicar filtro ciclos_forcados se fornecido
        if ciclos_forcados:
            ciclos_faltantes = [c for c in ciclos_faltantes if c in ciclos_forcados]
        ciclos = ciclos_faltantes
        print(f"  {len(ciclos)} ciclos × "
              f"{len(ohlcv_ativos)} ativos (apenas ausentes)")

        # ← MUDANÇA: inicializar score_hist e vol_hist do cache existente
        score_hist = {}
        vol_hist   = {}
        if not df_cache.empty:
            for ativo in self.ativos:
                df_ativo_cache = df_cache[df_cache["ativo"] == ativo].sort_values("ciclo_id")
                if not df_ativo_cache.empty:
                    # Usar últimos 6 ciclos para contexto histórico (Ridge calibration)
                    score_hist[ativo] = df_ativo_cache["score"].tolist()[-6:]
                    vol_hist[ativo] = df_ativo_cache["vol_21d"].tolist()[-6:]

        rows       = []

        # PATCH v3.5: cache configs - evita recarregar TAPE a cada ciclo
        cfgs_ativos = {ativo: tape_ativo_carregar(ativo) for ativo in ohlcv_ativos}

        for ciclo_id in _tqdm(ciclos, desc="ORBIT",
                             unit="ciclo", ncols=None):
            data_ref = self._data_ref(ciclo_id)

            for ativo in ohlcv_ativos:
                cfg = cfgs_ativos[ativo]

                df_ohlcv = ohlcv_ativos[ativo]
                df_ate   = df_ohlcv[
                    df_ohlcv.index.date <= data_ref
                ].copy()

                if len(df_ate) < JANELA_OLS + 63:
                    continue

                ibov_al = ibov_close.reindex(
                    df_ate.index, method="ffill")

                resultado = self.orbit_ativo_processar(
                    ativo, cfg, df_ate,
                    ibov_al, ciclo_id,
                    score_hist, vol_hist)

                if resultado:
                    rows.append(resultado)
                    try:
                        tape_ciclo_salvar(ativo, resultado)
                    except Exception as e:
                        emit_error(f"Falha ao salvar {ativo} {ciclo_id}: {e}")

        if not rows:
            print("  ✗ ORBIT sem resultados")
            return pd.DataFrame()

        df_regimes = pd.DataFrame(rows)
        df_regimes["ciclo_id"] = \
            df_regimes["ciclo_id"].astype(str)

        if modo == "mensal":
            self._relatorio(df_regimes)

        return df_regimes

    def orbit_ativo_processar(self, ativo, cfg, df_ohlcv,
                          ibov_close, ciclo_id,
                          score_hist_global=None,
                          vol_hist_global=None):
        if score_hist_global is None: score_hist_global = {}
        if vol_hist_global   is None: vol_hist_global   = {}

        idx = df_ohlcv.index.intersection(ibov_close.index)
        if len(idx) < JANELA_OLS + 63:
            return None

        df_at = df_ohlcv.loc[idx].copy()
        ib    = ibov_close.loc[idx].values

        externas_dict = {}
        for nome_serie, ativa in \
                cfg.get("externas", {}).items():
            if ativa and nome_serie in self._externas_cache:
                externas_dict[nome_serie] = \
                    self._externas_cache[nome_serie]

        cam = _calcular_camadas(
            df_at, ib,
            externas_dict if externas_dict else None)

        close_col = "close" if "close" in df_at.columns \
                    else "fechamento"
        ret_fut = df_at[close_col].pct_change(
            HORIZONTE_DIAS).shift(-HORIZONTE_DIAS)

        prior = cfg.get("prior")

        scores, ph = _score_rolante(
            cam, ret_fut, prior,
            JANELA_OLS, RECALIBRAR_DIAS, RIDGE_LAMBDA)

        if not ph:
            return None

        ir_treino = ph[-1]["ir"]

        data_ref_ts = pd.Timestamp(str(
            df_at.index[-1].date()))
        scores_ate_ref = scores.loc[
            scores.index <= data_ref_ts].dropna()
        sc_abs = scores_ate_ref.abs().values
        _thresh_fb = carregar_config()["orbit"]["threshold_fallback"]
        thresh = float(np.percentile(
            sc_abs, PERCENTIL_THRESHOLD)) \
                 if len(sc_abs) > 20 else _thresh_fb
        score_atual = float(
            scores_ate_ref.iloc[-1]) \
                      if not scores_ate_ref.empty \
                      else 0.0

        if ativo not in score_hist_global:
            score_hist_global[ativo] = []
        if ativo not in vol_hist_global:
            vol_hist_global[ativo]   = []

        vol_21d_atual = 0.0
        if "vol_21d" in df_at.columns:
            v = df_at["vol_21d"].dropna()
            if not v.empty:
                vol_21d_atual = float(v.iloc[-1])

        vol_63d_atual = 0.0
        if "vol_63d" in df_at.columns:
            v63 = df_at["vol_63d"].dropna()
            if not v63.empty:
                vol_63d_atual = float(v63.iloc[-1])

        score_hist_global[ativo].append(score_atual)
        vol_hist_global[ativo].append(vol_21d_atual)
        score_hist_global[ativo] = \
            score_hist_global[ativo][-6:]
        vol_hist_global[ativo]   = \
            vol_hist_global[ativo][-6:]

        hist     = score_hist_global[ativo]
        score_vel = round(float(
            (hist[-1] - hist[-3]) / 2
            if len(hist) >= 3 else 0.0), 4)

        regime = _classificar_regime(
            score_hist_global[ativo],
            vol_hist_global[ativo],
            thresh)

        if regime == "NEUTRO":
            regime = _classificar_sub_regime_neutro(
                score_atual,
                score_vel,
                vol_21d_atual,
                vol_63d_atual,
                thresh)

        df_p = pd.DataFrame({
            "score":      scores_ate_ref,
            "ret_futuro": ret_fut
        }, index=scores_ate_ref.index).dropna()

        pred = np.where(df_p["score"] >  thresh, "ALTA",
               np.where(df_p["score"] < -thresh, "BAIXA",
                                                  "NEUTRO"))
        ret  = df_p["ret_futuro"].values
        mask = pred != "NEUTRO"
        rs   = np.where(pred=="ALTA",  ret,
               np.where(pred=="BAIXA",-ret, 0))[mask]

        ir = (np.mean(rs)/(np.std(rs)+1e-10)*
              math.sqrt(252/HORIZONTE_DIAS)
              if len(rs) > 5 else 0.0)

        regimes_sizing = cfg.get(
            "regimes_sizing",
            carregar_config()["fire"]["regimes_sizing_padrao"])
        sizing = float(regimes_sizing.get(regime, 0.0))

        _ir_operar = cfg.get("ir_operar") or IR_OPERAR
        if ir < _ir_operar:
            sizing = 0.0
        elif ir < IR_MONITORAR:
            sizing = 0.0

        pesos_at = ph[-1]["pesos"]
        pct_n    = (pred=="NEUTRO").mean()*100

        return {
            "ciclo_id":   str(ciclo_id),
            "ativo":      ativo,
            "data_ref":   str(df_at.index[-1].date()),
            "regime_estrategia": regime,
            "ir":         round(float(ir),        4),
            "ir_treino":  round(float(ir_treino),  4),
            "sizing":     sizing,
            "score":      round(float(score_atual),4),
            "thresh":     round(float(thresh),     4),
            "score_vel":  score_vel,
            "vol_21d":    round(float(vol_21d_atual),4),
            "vol_63d":    round(float(vol_63d_atual),4),
            "pct_neutro": round(float(pct_n),      1),
            "s1": round(float(pesos_at.get("s1",0)),4),
            "s2": round(float(pesos_at.get("s2",0)),4),
            "s3": round(float(pesos_at.get("s3",0)),4),
            "s4": round(float(pesos_at.get("s4",0)),4),
            "s5": round(float(pesos_at.get("s5",0)),4),
            "s6": round(float(pesos_at.get("s6",0)),4)
                  if "s6" in pesos_at else 0.0,
        }

    def orbit_regime_para_data(self, ativo, data):
        return tape_ciclo_para_data(ativo, data)

    def _relatorio(self, df_regimes):
        ciclos = sorted(df_regimes["ciclo_id"].unique())
        if not ciclos: return
        ciclo_atual = ciclos[-1]
        ciclo_ant   = ciclos[-2] if len(ciclos)>=2 else None
        sep = "═"*60
        print(f"\n{sep}")
        print(f"  ORBIT v3.5 — Relatório {ciclo_atual}")
        print(sep)
        df_m0 = df_regimes[
            df_regimes["ciclo_id"]==ciclo_atual]
        df_m1 = df_regimes[
            df_regimes["ciclo_id"]==ciclo_ant] \
            if ciclo_ant else pd.DataFrame()

        print(f"  {'Ativo':8} {'Regime':12} {'IR':>7} "
              f"{'ΔIR':>7} {'Vel':>7} {'S6':>7} {'Sizing':>7}")
        print(f"  {'─'*60}")

        for _, row in df_m0.sort_values(
                "ir", ascending=False).iterrows():
            ativo  = row["ativo"]
            ir     = float(row["ir"])
            sizing = float(row["sizing"])
            vel    = float(row.get("score_vel",0))
            s6     = float(row.get("s6",0))

            if not df_m1.empty:
                r_ant  = df_m1[df_m1["ativo"]==ativo]
                ir_ant = float(r_ant["ir"].iloc[0]) \
                         if not r_ant.empty else None
                d_ir   = f"{ir-ir_ant:+.3f}" \
                         if ir_ant is not None else "  n/a"
            else:
                d_ir = "  n/a"

            if   ir >= IR_OPERAR:    status = "OPERAR   ✓"
            elif ir >= IR_MONITORAR: status = "MONITOR  ~"
            else:                    status = "EXCLUÍDO ✗"

            print(f"  {ativo:8} {row['regime']:12} "
                  f"{ir:>+7.3f} {d_ir:>7} "
                  f"{vel:>+7.3f} {s6:>7.3f} "
                  f"{sizing:>7.1f}  {status}")
        print(f"\n{sep}\n")

    def _gerar_ciclos(self, anos):
        ciclos = []
        for ano in sorted(anos):
            for mes in range(1,13):
                if date(ano,mes,1) <= date.today():
                    ciclos.append(f"{ano}-{mes:02d}")
        return ciclos

    def _data_ref(self, ciclo_id):
        ano,mes = int(ciclo_id[:4]),int(ciclo_id[5:])
        if mes==12:
            return date(ano+1,1,1)-timedelta(days=1)
        return date(ano,mes+1,1)-timedelta(days=1)

    def orbit_cache_carregar(self, anos):
        necessarios = set()
        for ano in anos:
            for mes in range(1,13):
                if date(ano,mes,1) <= date.today():
                    necessarios.add(f"{ano}-{mes:02d}")

        rows = []
        ciclos_existentes = set()
        for ativo in self.ativos:
            dados = tape_ativo_carregar(ativo)
            historico = dados.get("historico", [])
            for c in historico:
                ciclos_existentes.add(c["ciclo_id"])
                rows.append(c)

        ciclos_faltantes = sorted(necessarios - ciclos_existentes)

        if not rows:
            # Cache vazio — processar todos os ciclos
            print(f"  ~ Cache vazio — processando {len(ciclos_faltantes)} ciclos")
            return pd.DataFrame(), ciclos_faltantes

        df = pd.DataFrame(rows)
        df["ciclo_id"] = df["ciclo_id"].astype(str)

        if not ciclos_faltantes:
            # Cache completo — nada a processar
            print(f"  ✓ Cache completo — {len(df):,} registros, nenhum ciclo novo")
            return df, []

        # Cache parcial — ignorar ciclos anteriores ao primeiro registrado
        # (primeiros meses de 2002 são bootstrap, nunca foram salvos)
        if ciclos_faltantes and ciclos_existentes:
            primeiro_existente = min(ciclos_existentes)
            ciclos_faltantes = [c for c in ciclos_faltantes
                                if c >= primeiro_existente]

        if not ciclos_faltantes:
            print(f"  ✓ Cache completo — {len(df):,} registros, nenhum ciclo novo")
            return df, []

        print(f"  ~ Cache parcial — {len(ciclos_faltantes)} ciclo(s) ausente(s): {ciclos_faltantes[:3]}")
        return df, ciclos_faltantes

if __name__ == "__main__":
    print("✓ ORBIT v3.5 carregado")
    print("  5 regimes | dados via TAPE | master JSON por ativo")
    print("  tape_reflect_cycle removido — responsabilidade do EDGE")
    print("  ORBIT(universo).rodar(df_tape, anos, modo)")