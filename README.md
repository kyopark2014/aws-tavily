Tavily 검색 서비스를 AWS 계정으로 통합 과금하는 방법을 정리한 문서입니다. AWS Marketplace를 통한 구독으로 별도 결제 없이 AWS 청구서에 통합됩니다.

**🎯 핵심 요약**

- Tavily는 AWS Marketplace에 정식 등록되어 있음
- 별도 신용카드 등록 없이 AWS 계정으로 통합 청구 가능
- Enterprise Discount Program(EDP) 크레딧 적용 가능
- 한국에서는 원화 결제 및 세금계산서 발행 지원

**🛍️ Tavily의 AWS Marketplace 제품군**

- Tavily Enterprise: 엔터프라이즈급 검색 API (SOC 2 인증, SLA 포함, Zero Data Retention)
- Tavily MCP Server: Model Context Protocol 기반 서버 (Bedrock AgentCore와 연동 가능)

**🚀 통합 과금 설정 방식 1: AWS Marketplace 직접 구독 (가장 간단 ⭐)**

- AWS Console 로그인 → AWS Marketplace 진입
- 검색창에 Tavily 입력 후 제품 선택
- View purchase options 클릭 → 약관 동의 → Subscribe 클릭
- 구독 완료 후 Tavily 사용료가 AWS 통합 청구서에 자동 합산

**🤖 통합 과금 설정 방식 2: Bedrock AgentCore와 연동 배포 (추천)**

Tavily MCP Server를 Bedrock AgentCore Runtime에 직접 배포하여 AI 에이전트가 실시간 웹 검색을 사용할 수 있도록 합니다. AWS Marketplace에서 제공하는 컨테이너 이미지를 그대로 사용할 수 있어요.

**💼 통합 과금 설정 방식 3: Private Offer (대량 사용 시)**

- 대규모 사용량이라면 Tavily 영업팀과 협상하여 맞춤 가격으로 계약 가능
- EULA 맞춤 조건, 결제 스케줄 조정, 다년 계약 가능
- 기업 구매 프로세스(PO 발행 등)와 연동 가능

**🏢 여러 AWS 계정 통합 과금 (AWS Organizations)**

회사에서 여러 AWS 계정을 쓴다면 AWS Organizations의 Consolidated Billing 기능으로 관리합니다.

- Management Account(마스터 아카운트)에서 Tavily 구독 → 조직 내 다른 계정도 사용 가능
- 전체 조직의 비용이 마스터 계정의 단일 청구서로 수신
- Cost Allocation Tags로 부서별/프로젝트별 비용 분배 가능

**💎 AWS Marketplace 통합 과금의 장점**

- 단일 청구서: AWS 사용료와 Tavily 사용료가 하나의 청구서에 통합
- 별도 결제 수단 불필요: 신용카드 추가 등록 불필요
- 비용 가시성: AWS Cost Explorer에서 통합 분석 가능
- 태그 기반 분배: 부서/프로젝트별 비용 분류
- EDP 크레딧 사용 가능: Enterprise Discount Program 혁택 수혜
- 보안 통합: IAM 권한으로 접근 제어
- PO 발행 가능: 기업 구매 프로세스와 연동

**📊 비용 추적 팁**

- Cost Allocation Tags 활성화: Marketplace 구독 시 Project, Department, CostCenter 등 태그 추가
- AWS Cost Explorer에서 Service: AWS Marketplace, Vendor: Tavily 필터로 월별 사용량 확인
- AWS Budgets로 월 임계액 초과 시 알림 설정 (예: 월 $500 초과 시 이메일)

**🆚 직접 결제 vs Marketplace 통합 결제 비교**

- 결제 수단: 직접(신용카드 별도) vs Marketplace(AWS 계정과 통합)
- 청구서: 직접(Tavily 별도 발송) vs Marketplace(AWS 통합 청구서)
- 회계 처리: 직접(별도 벤더 등록) vs Marketplace(AWS와 동일 처리)
- 할인: 직접(Tavily 자체 할인) vs Marketplace(EDP 크레딧 적용 가능)
- 한국 법인 결제: 직접(USD 해외 결제) vs Marketplace(원화 결제 가능)

**🇰🇷 한국 사용자에게 특히 좋은 점**

- 원화 결제 가능 (AWS Korea 법인을 통해)
- 세금계산서 발행 가능
- 연간 계약 시 환율 고정 가능
- PO 기반 결제 지원 (기업 구매 프로세스)

**🤔 사용 규모별 추천 시나리오**

- 개인/소규모 테스트: Tavily 직접 가입 (Free Plan)
- 중규모 프로덕션: AWS Marketplace 표준 구독 ⭐
- 대규모 엔터프라이즈: AWS Marketplace Private Offer + EDP 활용 💎
- MCP 기반 에이전트: AWS Marketplace MCP Server + Bedrock AgentCore

**📚 참고 링크**

- Tavily Enterprise on AWS Marketplace
- Tavily MCP Server on AWS Marketplace
- Tavily + Bedrock AgentCore 통합 가이드
- AWS Marketplace Consolidated Billing 블로그
- Tavily 공식 Pricing 페이지
