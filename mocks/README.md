# CONTRATO: CanaSwarm-Intelligence

## ✅ CONTRATO DEFINIDO E TESTADO

### 🎯 O que este projeto RECEBE

**De:** Precision-Agriculture-Platform

**Via:** HTTP GET request

**Endpoint consumido:** `GET http://localhost:5000/api/v1/recommendations?field_id={id}`

**Formato:** JSON

**Frequência:** Sob demanda (dashboard tempo real) ou batch diário (histórico)

### Dados recebidos:

```json
{
  "field_id": "...",
  "zones": [
    {
      "zone_id": "...",
      "area_ha": 50.2,
      "profitability_score": 0.32,
      "recommendation": { "action": "reform", "priority": "high" },
      "financial_impact": { "estimated_loss_brl_year": 120000 }
    }
  ],
  "summary": { "total_estimated_impact_brl": 158000 }
}
```

---

### 🎯 O que este projeto PRODUZ

**Para:** Dashboard web (frontend) + Histórico (banco de dados)

**Processa:**
1. Exibe recomendações em tempo real no dashboard
2. Gera alertas para zonas críticas (profitability_score < 0.4)
3. Armazena histórico de análises
4. Compara ROI entre diferentes zonas
5. Ranking de prioridades de intervenção

**Output:**
- Dashboard visual com mapas + gráficos
- Alertas automáticos (email/SMS para zonas críticas)
- Relatórios gerenciais (PDF)

---

## ✅ Mock Funcional

Consumer testado e validado.

**Arquivos:**
- `consumer_mock.py` — Script que consome API do Precision
- `requirements.txt` — Dependências

**Como executar:**
```bash
# Terminal 1: Iniciar API do Precision
cd ../Precision-Agriculture-Platform/mocks
python api_mock.py

# Terminal 2: Consumir dados
cd ../CanaSwarm-Intelligence/mocks
pip install -r requirements.txt
python consumer_mock.py F001-UsinaGuarani-Piracicaba
```

---

## ✅ Teste Realizado

**Data:** 20/02/2026

**Resultado:** ✅ Consumer conectou, buscou, processou e exibiu dados com sucesso

**Output do teste:**
```
🧠 CanaSwarm-Intelligence - Dashboard Mock
🎯 Consultando recomendações para: F001-UsinaGuarani-Piracicaba
✅ Dados recebidos com sucesso!

📊 DASHBOARD - VISÃO GERAL
💰 IMPACTO FINANCEIRO TOTAL: R$ 158,000.00 / ano

🗺️  ANÁLISE POR ZONA
🔴 ZONA Z001 - 50.2 ha
  Recomendação: REFORM (prioridade high)
  💸 Prejuízo estimado: R$ 120,000.00 / ano

🟢 ZONA Z002 - 79.8 ha
  Recomendação: MAINTAIN (prioridade low)
  💰 Ganho estimado: R$ 50,000.00 / ano

🎯 INTEGRAÇÃO PRECISION → INTELLIGENCE: SUCESSO
```

---

**Status:** ✅ CONTRATO VALIDADO — Integração funcionando

**Evidência:** [INTEGRATION-PROOF.md](../../INTEGRATION-PROOF.md)
