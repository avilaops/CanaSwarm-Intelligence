#!/usr/bin/env python3
"""
Mock Consumer do CanaSwarm-Intelligence
Consome dados do Precision-Agriculture-Platform e exibe no dashboard simulado

USO:
    # 1. Inicie api_mock.py do Precision-Platform
    # 2. Execute este script:
    python consumer_mock.py F001-UsinaGuarani-Piracicaba
"""

import sys
import requests
import json
from datetime import datetime

# Config
PRECISION_API_URL = "http://localhost:5000/api/v1/recommendations"

def consume_recommendations(field_id: str):
    """
    Consome API do Precision-Platform e processa para dashboard
    """
    print("\n🧠 CanaSwarm-Intelligence - Dashboard Mock")
    print("=" * 70)
    print(f"🎯 Consultando recomendações para: {field_id}")
    print(f"🔗 API: {PRECISION_API_URL}")
    print("=" * 70)
    print()
    
    try:
        # Chamar API
        response = requests.get(PRECISION_API_URL, params={"field_id": field_id}, timeout=5)
        
        if response.status_code != 200:
            print(f"❌ Erro: {response.status_code}")
            print(response.json())
            return
        
        data = response.json()
        
        # Processar dados para dashboard
        print("✅ Dados recebidos com sucesso!\n")
        
        # HEADER
        print("📊 DASHBOARD - VISÃO GERAL")
        print("-" * 70)
        print(f"Talhão: {data['field_id']}")
        print(f"Cultura: {data['crop'].upper()} | Safra: {data['season']} | Corte: {data['harvest_number']}")
        print(f"Área total: {data['total_area_ha']} ha")
        print(f"Data da análise: {data['analysis_date']}")
        print()
        
        # SUMMARY
        summary = data['summary']
        print("💰 IMPACTO FINANCEIRO TOTAL")
        print("-" * 70)
        print(f"Impacto estimado: R$ {summary['total_estimated_impact_brl']:,.2f} / ano")
        print(f"Score médio de rentabilidade: {summary['avg_profitability_score']:.2f}")
        print()
        
        # ZONES
        print("🗺️  ANÁLISE POR ZONA")
        print("-" * 70)
        
        for zone in data['zones']:
            status_emoji = {
                'critical': '🔴',
                'warning': '🟡',
                'optimal': '🟢'
            }.get(zone['status'], '⚪')
            
            print(f"\n{status_emoji} ZONA {zone['zone_id']} - {zone['area_ha']} ha")
            print(f"  Produtividade: {zone['avg_yield_t_ha']:.1f} t/ha (esperado: {zone['expected_yield_t_ha']:.1f})")
            print(f"  Score: {zone['profitability_score']:.2f}")
            print(f"  Recomendação: {zone['recommendation']['action'].upper()} (prioridade {zone['recommendation']['priority']})")
            print(f"  Motivo: {zone['recommendation']['reason']}")
            
            impact = zone['financial_impact']
            if 'estimated_loss_brl_year' in impact:
                print(f"  💸 Prejuízo estimado: R$ {impact['estimated_loss_brl_year']:,.2f} / ano")
                if 'reform_cost_brl' in impact:
                    print(f"  💰 Custo de reforma: R$ {impact['reform_cost_brl']:,.2f}")
                    print(f"  ⏱️  Payback: {impact['payback_months']} meses")
            elif 'estimated_gain_brl_year' in impact:
                print(f"  💰 Ganho estimado: R$ {impact['estimated_gain_brl_year']:,.2f} / ano")
        
        print()
        print("=" * 70)
        print("🎯 INTEGRAÇÃO PRECISION → INTELLIGENCE: SUCESSO")
        print("=" * 70)
        print()
        
        # Salvar localmente (simulando armazenamento no dashboard)
        output_file = f"dashboard_data_{field_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Dados salvos em: {output_file}")
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("💡 Certifique-se de que api_mock.py está rodando em http://localhost:5000")
        print()
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\n❌ Uso: python consumer_mock.py <field_id>")
        print("📝 Exemplo: python consumer_mock.py F001-UsinaGuarani-Piracicaba\n")
        sys.exit(1)
    
    field_id = sys.argv[1]
    consume_recommendations(field_id)
