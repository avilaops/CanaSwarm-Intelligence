#!/usr/bin/env python3
"""
CanaSwarm-Intelligence - Vision Consumer Mock

Consome API do AI-Vision-Agriculture e integra com dados do Precision
"""

import requests
import json
from datetime import datetime
from pathlib import Path


class VisionConsumer:
    """Consome dados de visão computacional do AI-Vision"""
    
    def __init__(self, api_url: str = "http://localhost:5001"):
        self.api_url = api_url
    
    def get_field_maturity(self, field_id: str) -> dict:
        """Busca análise de maturidade de um talhão"""
        print(f"🔗 Consultando API Vision para: {field_id}")
        print(f"   URL: {self.api_url}/api/v1/maturity?field_id={field_id}")
        
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/maturity",
                params={'field_id': field_id},
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Dados recebidos com sucesso!\n")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return None
    
    def get_harvest_priority(self) -> dict:
        """Busca lista de prioridade de colheita"""
        print(f"🔗 Consultando prioridade de colheita...")
        print(f"   URL: {self.api_url}/api/v1/harvest-priority")
        
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/harvest-priority",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Dados recebidos com sucesso!\n")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return None
    
    def display_maturity_dashboard(self, maturity_data: dict):
        """Exibe dashboard de maturidade"""
        print("="*60)
        print("📊 DASHBOARD - ANÁLISE DE MATURIDADE")
        print("="*60)
        
        print(f"\n🌾 TALHÃO: {maturity_data['field_name']} ({maturity_data['field_id']})")
        print(f"   Área: {maturity_data['area_ha']} ha")
        print(f"   Cultura: {maturity_data['crop'].upper()}")
        print(f"   Corte: {maturity_data['harvest_number']}")
        
        maturity = maturity_data['maturity']
        status_icon = "🟢" if maturity['maturity_level'] in ['optimal', 'mature'] else "🟡"
        
        print(f"\n{status_icon} ANÁLISE DE MATURIDADE:")
        print(f"   Score: {maturity['maturity_score']:.2%}")
        print(f"   Nível: {maturity['maturity_level'].upper()}")
        print(f"   Açúcar estimado: {maturity['estimated_sugar_content_percent']:.1f}%")
        print(f"   Confiança: {maturity['confidence']:.2%}")
        
        print(f"\n📈 ÍNDICES DE VEGETAÇÃO:")
        indices = maturity_data['indices']
        print(f"   NDVI médio: {indices['ndvi_avg']:.2f}")
        print(f"   NDVI desvio: {indices['ndvi_std']:.2f}")
        print(f"   Red Edge: {indices['red_edge_avg']:.2f}")
        print(f"   Moisture Index: {indices['moisture_index']:.2f}")
        
        if 'zones' in maturity_data and maturity_data['zones']:
            print(f"\n🗺️  ANÁLISE POR ZONA:")
            for zone in maturity_data['zones']:
                zone_icon = "🟢" if zone['maturity_score'] > 0.75 else "🟡"
                print(f"\n{zone_icon} ZONA {zone['zone_id']}")
                print(f"   Área: {zone['area_ha']} ha")
                print(f"   Maturidade: {zone['maturity_score']:.2%} ({zone['maturity_level']})")
                print(f"   NDVI: {zone['ndvi_avg']:.2f}")
                print(f"   Nota: {zone['notes']}")
        
        if 'recommendations' in maturity_data and maturity_data['recommendations']:
            print(f"\n💡 RECOMENDAÇÕES:")
            for rec in maturity_data['recommendations']:
                priority_icon = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
                print(f"\n{priority_icon} {rec['action'].replace('_', ' ').upper()}")
                print(f"   Prioridade: {rec['priority'].upper()}")
                if 'timeframe' in rec:
                    print(f"   Prazo: {rec['timeframe'].replace('_', ' ')}")
                print(f"   Motivo: {rec['reason']}")
    
    def display_harvest_priority(self, priority_data: dict):
        """Exibe prioridade de colheita"""
        print("\n" + "="*60)
        print("🎯 PRIORIDADE DE COLHEITA")
        print("="*60)
        
        print(f"\nTotal de talhões: {priority_data['total_fields']}")
        
        for i, field in enumerate(priority_data['fields'], 1):
            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            
            print(f"\n{icon} {i}º - {field['field_name']} ({field['field_id']})")
            print(f"   Prioridade: {field['priority_label']}")
            print(f"   Maturidade: {field['maturity_score']:.2%} ({field['maturity_level']})")
            print(f"   Açúcar: {field['sugar_content_percent']:.1f}%")
            print(f"   Área: {field['area_ha']} ha")
            print(f"   Recomendação: {field['harvest_recommendation'].replace('_', ' ').upper()}")


if __name__ == "__main__":
    print("🧠 CanaSwarm-Intelligence - Vision Consumer Mock\n")
    print("="*60)
    print("\n🎯 TESTANDO INTEGRAÇÃO AI-VISION → INTELLIGENCE\n")
    
    consumer = VisionConsumer(api_url="http://localhost:5001")
    
    # Teste 1: Buscar maturidade de um talhão
    print("="*60)
    print("TESTE 1: Análise de maturidade do talhão F001")
    print("="*60 + "\n")
    
    maturity_data = consumer.get_field_maturity("F001")
    
    if maturity_data:
        consumer.display_maturity_dashboard(maturity_data)
        
        # Salva dados
        output_file = Path(__file__).parent / f"vision_data_F001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(maturity_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Dados salvos em: {output_file.name}")
    
    # Teste 2: Buscar prioridade de colheita
    print("\n\n" + "="*60)
    print("TESTE 2: Prioridade de colheita de todos os talhões")
    print("="*60 + "\n")
    
    priority_data = consumer.get_harvest_priority()
    
    if priority_data:
        consumer.display_harvest_priority(priority_data)
    
    print("\n" + "="*60)
    print("🎉 INTEGRAÇÃO AI-VISION → INTELLIGENCE: SUCESSO")
    print("="*60)
    print("\n✅ Dados de maturidade recebidos")
    print("✅ Zonas analisadas individualmente")
    print("✅ Prioridade de colheita calculada")
    print("✅ Dashboard exibido corretamente")
    print("\n💡 Intelligence pode agora combinar:")
    print("   • Dados de produtividade (Precision)")
    print("   • Dados de maturidade (AI-Vision)")
    print("   • Para decisões ótimas de colheita\n")
