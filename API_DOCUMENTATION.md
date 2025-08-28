# 🚀 혜택 추천 챗봇 API 문서

## 📋 목차

1. [개요](#개요)
2. [빠른 시작](#빠른-시작)
3. [엔드포인트](#엔드포인트)
4. [데이터 모델](#데이터-모델)
5. [Flutter 통합 가이드](#flutter-통합-가이드)
6. [에러 처리](#에러-처리)

---

## 📖 개요

### 서비스 소개
AI 기반 개인화된 혜택 추천 및 챗봇 서비스 API입니다. 사용자의 소비 패턴을 분석하여 맞춤형 혜택을 제공합니다.

### 주요 기능
- 🤖 **자연어 챗봇**: 대화형 혜택 검색 및 추천
- 🎯 **개인화 추천**: 소비 패턴 기반 맞춤형 혜택
- 🔍 **실시간 웹 검색**: 부족한 결과 자동 보완
- 📊 **소비 분석**: 사용자 행동 패턴 분석

### 기술 스택
- **Backend**: Flask + Gunicorn
- **AI**: CLOVA Studio API
- **Database**: ChromaDB (Vector Database)
- **Web Server**: Nginx
- **Deployment**: AWS EC2

---

## 🚀 빠른 시작

### 기본 정보
- **Base URL**: `http://your-server-ip` 또는 `https://your-domain.com`
- **API Version**: 2.1.0-ec2
- **Content-Type**: `application/json`
- **Authentication**: 없음 (현재 버전)

### 첫 번째 요청

```bash
# 헬스체크
curl -X GET http://your-server-ip/health

# 챗봇 메시지 전송
curl -X POST http://your-server-ip/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "스타벅스 혜택 알려주세요",
    "user_id": "test_user_123"
  }'
```

---

## 📡 엔드포인트

### 1. 챗봇 메시지 전송 ⭐ **[추천]**

가장 핵심적인 API입니다. Flutter 앱에서 주로 사용하세요.

```http
POST /api/chat
```

#### 특징
- 자연어 질문 처리
- 자동 웹 검색 보완 (결과 부족 시)
- 개인화된 응답 생성
- 추천 질문 제공

#### 요청 예시

```json
{
  "message": "스타벅스 혜택 알려주세요",
  "user_id": "flutter_user_12345",
  "user_context": {
    "spending_history": [
      {
        "brand": "스타벅스",
        "category": "카페",
        "amount": 5000,
        "date": "2024-01-15"
      }
    ]
  }
}
```

#### 응답 예시

```json
{
  "success": true,
  "response": {
    "message": "스타벅스 관련 혜택을 찾았습니다! 🎉\n\n1. **스타벅스 사이렌오더** - 별 적립 혜택\n구매 금액의 2% 별 적립\n\n2. **신한카드 스타벅스 혜택** - 10% 할인\n신한카드 결제 시 매월 5만원 한도",
    "timestamp": "2024-01-20T10:30:00Z",
    "data": {
      "total_results": 5,
      "web_search_used": false,
      "search_strategy": {
        "categories_found": ["카페"],
        "brands_found": ["스타벅스"]
      },
      "suggestions": [
        "이디야 혜택도 알려주세요",
        "카페 할인카드 추천해주세요"
      ]
    }
  },
  "search_results": [
    {
      "id": "benefit_001",
      "metadata": {
        "title": "스타벅스 사이렌오더 적립",
        "brand": "스타벅스",
        "category": "카페",
        "benefit_type": "적립",
        "discount_rate": "별 1개당 12.5원",
        "conditions": "사이렌오더 결제 시",
        "valid_from": "2024-01-01",
        "valid_to": "2024-12-31",
        "source": "내부데이터"
      },
      "similarity_score": 0.95,
      "search_type": "direct_brand"
    }
  ]
}
```

### 2. 혜택 검색

```http
POST /api/search
```

#### 요청 예시

```json
{
  "query": "카페 할인",
  "user_history": {
    "preferred_brands": ["스타벅스", "이디야"],
    "preferred_categories": ["카페"]
  },
  "top_k": 5,
  "debug": false
}
```

#### 응답 예시

```json
{
  "success": true,
  "query": "카페 할인",
  "extracted_categories": ["카페"],
  "extracted_brands": [],
  "results": [
    {
      "id": "benefit_002",
      "metadata": {
        "title": "이디야 할인 혜택",
        "brand": "이디야",
        "category": "카페",
        "benefit_type": "할인",
        "discount_rate": "10%",
        "conditions": "멤버십 가입 시",
        "valid_from": "2024-01-01",
        "valid_to": "2024-12-31"
      },
      "similarity_score": 0.88
    }
  ],
  "total_found": 3,
  "web_search_used": true,
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 3. AI 개인화 추천

```http
POST /api/recommend
```

#### 요청 예시

```json
{
  "query": "맞춤 혜택 추천",
  "user_profile": {
    "preferred_brands": ["스타벅스", "맥도날드"],
    "preferred_categories": ["카페", "패스트푸드"],
    "total_transactions": 50,
    "average_spending": {
      "카페": 4500,
      "패스트푸드": 8000
    }
  },
  "spending_history": [
    {
      "brand": "스타벅스",
      "category": "카페",
      "amount": 5000,
      "date": "2024-01-15"
    }
  ],
  "top_k": 10
}
```

#### 응답 예시

```json
{
  "success": true,
  "query": "맞춤 혜택 추천",
  "ai_response": "고객님의 소비 패턴을 분석한 결과, 카페와 패스트푸드 이용이 많은 것으로 확인됩니다. 이에 맞는 최적의 혜택을 추천드립니다.",
  "search_results": [...],
  "user_profile_summary": {
    "total_transactions": 50,
    "preferred_brands": ["스타벅스", "맥도날드"],
    "profile_strength": "strong"
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 4. 헬스체크

```http
GET /health
```

#### 응답 예시

```json
{
  "status": "healthy",
  "service": "EC2 개인화된 혜택 추천 API v2.1",
  "database_connected": true,
  "rag_system_loaded": true,
  "version": "2.1.0-ec2",
  "timestamp": "2024-01-20T10:30:00Z",
  "environment": "production"
}
```

### 5. 카테고리 목록 조회

```http
GET /api/categories
```

#### 응답 예시

```json
{
  "categories": [
    "카페",
    "마트",
    "편의점",
    "온라인쇼핑",
    "배달음식",
    "뷰티",
    "패스트푸드",
    "주유소"
  ],
  "category_details": {
    "카페": ["카페", "커피", "coffee", "스타벅스", "이디야"],
    "마트": ["마트", "mart", "슈퍼", "이마트", "홈플러스"]
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 6. API 정보

API 버전, 기능, 엔드포인트 정보를 제공합니다.

```http
GET /api/info
```

#### 응답 예시

```json
{
  "service_name": "혜택 추천 챗봇 API",
  "version": "2.1.0-ec2",
  "description": "AI 기반 개인화된 혜택 추천 및 챗봇 서비스",
  "deployment": "EC2 Production",
  "features": [
    "자연어 챗봇",
    "개인화 추천",
    "웹 검색 보완",
    "소비 패턴 분석"
  ],
  "endpoints": {
    "chat": "/api/chat",
    "search": "/api/search",
    "recommend": "/api/recommend",
    "health": "/health",
    "categories": "/api/categories",
    "analyze_image": "/api/analyze-image"
  },
  "status": "operational",
  "database_status": "connected"
}
```

### 7. 데이터베이스 통계

데이터베이스 연결 상태와 통계 정보를 제공합니다.

```http
GET /api/stats
```

#### 응답 예시

```json
{
  "status": "healthy",
  "total_documents": 1250,
  "available_brands": 45,
  "available_categories": 8,
  "collection_name": "cafe_benefits",
  "db_path": "/opt/benefits-api/data/cafe_vector_db",
  "metadata_loaded": true,
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 8. 이미지 OCR 분석 및 브랜드 매칭 ⭐ **[신규]**

이미지를 업로드하면 Clova OCR로 텍스트를 추출하고, 해당 날짜의 챗봇 대화 데이터와 매칭하여 브랜드를 찾는 API입니다.

```http
POST /api/analyze-image
```

#### 특징
- 이미지에서 텍스트 및 날짜 자동 추출
- 해당 날짜의 챗봇 대화 데이터와 브랜드 매칭
- Clova X AI를 활용한 지능형 브랜드 분석
- 다양한 이미지 형식 지원 (JPEG, PNG, BMP)

#### 요청 예시

```bash
# cURL 예시
curl -X POST http://your-server-ip/api/analyze-image \
  -F "image=@receipt.jpg" \
  -F "debug=true"
```

```javascript
// JavaScript 예시
const formData = new FormData();
formData.append('image', imageFile);
formData.append('debug', 'true');

const response = await fetch('/api/analyze-image', {
  method: 'POST',
  body: formData
});
```

```dart
// Flutter 예시
import 'dart:io';
import 'package:http/http.dart' as http;

Future<Map<String, dynamic>> analyzeImage(File imageFile) async {
  var request = http.MultipartRequest(
    'POST',
    Uri.parse('http://your-server-ip/api/analyze-image'),
  );
  
  request.files.add(
    await http.MultipartFile.fromPath('image', imageFile.path),
  );
  request.fields['debug'] = 'true';
  
  var response = await request.send();
  var responseData = await response.stream.bytesToString();
  
  return json.decode(responseData);
}
```

#### 응답 예시

```json
{
  "success": true,
  "data": {
    "extracted_text": "스타벅스 아메리카노 4,500원 2025-08-15",
    "extracted_date": "2025-08-15",
    "matched_brands": ["스타벅스"],
    "confidence_scores": {
      "스타벅스": 0.95
    },
    "analysis_summary": "이미지에서 '스타벅스' 브랜드가 명확하게 식별되었으며, 해당 날짜의 챗봇 대화에서도 동일한 브랜드가 언급되어 높은 신뢰도로 매칭되었습니다."
  },
  "message": "이미지 분석 완료: 1개 브랜드 매칭"
}
```

#### 지원 이미지 형식
- **JPEG/JPG**: 가장 일반적인 형식, 압축률 조절 가능
- **PNG**: 투명도 지원, 무손실 압축
- **BMP**: 비트맵 형식, 품질 우수

#### 이미지 요구사항
- **최소 크기**: 100x100 픽셀
- **최대 크기**: 10MB
- **권장 해상도**: 800x600 이상 (텍스트 가독성 향상)

#### 사용 시나리오
1. **영수증 분석**: 카페, 식당 영수증에서 브랜드 및 날짜 추출
2. **쿠폰 인식**: 할인 쿠폰 이미지에서 브랜드 정보 추출
3. **명함 스캔**: 비즈니스 명함에서 회사명 및 연락처 추출
4. **문서 분석**: 공지사항, 안내문에서 중요 정보 추출

#### 에러 응답 예시

```json
{
  "success": false,
  "error": "이미지 파일이 너무 큽니다. 10MB 이하여야 합니다.",
  "extracted_text": "",
  "extracted_date": null,
  "matched_brands": []
}
```

#### 디버그 모드
`debug=true` 파라미터를 추가하면 상세한 분석 과정을 로그로 확인할 수 있습니다.

```json
{
  "success": true,
  "data": {
    "extracted_text": "이디야 커피 3,000원 2025-08-15",
    "extracted_date": "2025-08-15",
    "matched_brands": ["이디야"],
    "confidence_scores": {
      "이디야": 0.88
    },
    "analysis_summary": "OCR을 통해 '이디야' 브랜드가 식별되었으며, 챗봇 대화 데이터와 매칭하여 브랜드 정보를 제공합니다."
  },
  "message": "이미지 분석 완료: 1개 브랜드 매칭"
}
```

---

## 📊 데이터 모델

### ChatRequest
```json
{
  "message": "string",           // 사용자 메시지/질문 (필수)
  "user_id": "string",           // 고유 사용자 ID (필수)
  "user_context": {              // 사용자 컨텍스트 정보 (선택)
    "spending_history": [        // 소비 이력
      {
        "brand": "string",       // 브랜드명
        "category": "string",    // 카테고리
        "amount": "number",      // 소비 금액
        "date": "string"         // 소비 날짜 (YYYY-MM-DD)
      }
    ]
  }
}
```

### ChatResponse
```json
{
  "success": "boolean",          // 요청 성공 여부
  "response": {                  // 응답 데이터
    "message": "string",         // AI 생성 응답 메시지
    "timestamp": "string",       // 응답 생성 시간
    "data": {                    // 메타데이터
      "total_results": "number", // 총 검색 결과 수
      "web_search_used": "boolean", // 웹 검색 보완 사용 여부
      "search_strategy": {       // 사용된 검색 전략 정보
        "categories_found": ["string"],
        "brands_found": ["string"]
      },
      "suggestions": ["string"]  // 추천 질문 목록
    }
  },
  "search_results": [            // 검색된 혜택 결과 목록
    {
      "id": "string",            // 혜택 고유 ID
      "metadata": {              // 혜택 메타데이터
        "title": "string",       // 혜택 제목
        "brand": "string",       // 브랜드명
        "category": "string",    // 카테고리
        "benefit_type": "string", // 혜택 유형
        "discount_rate": "string", // 할인율 또는 혜택 정도
        "conditions": "string",  // 혜택 조건
        "valid_from": "string",  // 유효기간 시작
        "valid_to": "string",    // 유효기간 종료
        "source": "string",      // 데이터 출처
        "url": "string"          // 관련 웹사이트 URL (선택)
      },
      "similarity_score": "number", // 유사도 점수 (0-1)
      "search_type": "string"    // 검색 방식
    }
  ],
  "error": "string"              // 오류 메시지 (실패 시)
}
```

### SearchRequest
```json
{
  "query": "string",             // 검색 질의 (필수)
  "user_history": {              // 사용자 이력 정보 (선택)
    "preferred_brands": ["string"],
    "preferred_categories": ["string"]
  },
  "top_k": "number",             // 반환할 최대 결과 수 (기본값: 5)
  "debug": "boolean"             // 디버그 모드 (기본값: false)
}
```

### BenefitMetadata
```json
{
  "title": "string",             // 혜택 제목
  "brand": "string",             // 브랜드명
  "category": "string",          // 카테고리
  "benefit_type": "string",      // 혜택 유형 (할인, 적립, 쿠폰 등)
  "discount_rate": "string",     // 할인율 또는 혜택 정도
  "conditions": "string",        // 혜택 조건
  "valid_from": "string",        // 유효기간 시작
  "valid_to": "string",          // 유효기간 종료
  "source": "string",            // 데이터 출처
  "url": "string",               // 관련 웹사이트 URL (웹 검색 결과의 경우)
  "search_keyword": "string"     // 웹 검색에 사용된 키워드 (웹 검색 결과의 경우)
}
```

### ImageAnalysisRequest
```json
{
  "image": "file",               // 이미지 파일 (multipart/form-data)
  "debug": "boolean"             // 디버그 모드 (기본값: false)
}
```

### ImageAnalysisResponse
```json
{
  "success": "boolean",          // 요청 성공 여부
  "data": {                      // 분석 결과 데이터
    "extracted_text": "string",  // OCR로 추출된 텍스트
    "extracted_date": "string",  // 추출된 날짜 (YYYY-MM-DD)
    "matched_brands": ["string"], // 매칭된 브랜드 목록
    "confidence_scores": {       // 브랜드별 신뢰도 점수
      "brand_name": "number"     // 0.0-1.0 사이의 신뢰도
    },
    "analysis_summary": "string" // AI 분석 요약
  },
  "message": "string",           // 결과 메시지
  "error": "string"              // 오류 메시지 (실패 시)
}
```

---

## ❌ 에러 처리

### 공통 에러 응답 형식

```json
{
  "success": false,
  "error": "오류 메시지",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### HTTP 상태 코드

| 코드 | 설명 | 예시 |
|------|------|------|
| 200 | 성공 | 요청이 정상적으로 처리됨 |
| 400 | 잘못된 요청 | 필수 파라미터 누락, 형식 오류 |
| 500 | 서버 내부 오류 | 시스템 오류, 데이터베이스 연결 실패 |
| 503 | 서비스 사용 불가 | RAG 시스템 초기화 실패 |

### 주요 에러 메시지

| 에러 코드 | 메시지 | 해결 방법 |
|-----------|--------|-----------|
| MISSING_PARAMETER | 필수 파라미터가 누락되었습니다 | message, user_id 등 필수 필드 확인 |
| INVALID_FORMAT | 잘못된 데이터 형식입니다 | JSON 형식 및 데이터 타입 확인 |
| RAG_SYSTEM_ERROR | RAG 시스템이 초기화되지 않았습니다 | 서버 재시작 또는 관리자 문의 |
| DATABASE_ERROR | 데이터베이스 연결 오류입니다 | 데이터베이스 상태 확인 |
| AI_SERVICE_ERROR | AI 서비스 오류가 발생했습니다 | API 키 설정 및 서비스 상태 확인 |

---

## 📱 Flutter 통합 가이드

### 1. HTTP 패키지 설정

```yaml
# pubspec.yaml
dependencies:
  http: ^1.1.0
  flutter:
    sdk: flutter
```

### 2. API 서비스 클래스

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class BenefitsApiService {
  static const String baseUrl = 'http://your-server-ip';

  // 챗봇 메시지 전송
  Future<Map<String, dynamic>> sendChatMessage({
    required String message,
    required String userId,
    List<Map<String, dynamic>>? spendingHistory,
  }) async {
    final url = Uri.parse('$baseUrl/api/chat');

    final body = {
      'message': message,
      'user_id': userId,
      'user_context': {
        'spending_history': spendingHistory ?? []
      }
    };

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: json.encode(body),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw ApiException('HTTP ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      throw ApiException('네트워크 오류: $e');
    }
  }

  // 혜택 검색
  Future<Map<String, dynamic>> searchBenefits({
    required String query,
    Map<String, dynamic>? userHistory,
    int topK = 5,
  }) async {
    final url = Uri.parse('$baseUrl/api/search');

    final body = {
      'query': query,
      'user_history': userHistory,
      'top_k': topK,
      'debug': false,
    };

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw ApiException('검색 실패: ${response.statusCode}');
    }
  }

  // 헬스체크
  Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
        headers: {'Accept': 'application/json'},
      ).timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // 카테고리 목록
  Future<List<String>> getCategories() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/categories'),
      headers: {'Accept': 'application/json'},
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<String>.from(data['categories']);
    } else {
      throw ApiException('카테고리 조회 실패');
    }
  }

  // 이미지 OCR 분석 (상세 구현은 API_SPEC_FLUTTER.md 참조)
  Future<Map<String, dynamic>> analyzeImage({
    required File imageFile,
    bool debug = false,
  }) async {
    // 이미지 분석 로직 구현
    // 상세 코드는 API_SPEC_FLUTTER.md 파일을 참조하세요
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);

  @override
  String toString() => 'ApiException: $message';
}
```

### 3. 데이터 모델

```dart
class ChatResponse {
  final bool success;
  final ChatData? response;
  final String? error;
  final List<SearchResult>? searchResults;

  ChatResponse({
    required this.success,
    this.response,
    this.error,
    this.searchResults,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) {
    return ChatResponse(
      success: json['success'] ?? false,
      response: json['response'] != null
          ? ChatData.fromJson(json['response'])
          : null,
      error: json['error'],
      searchResults: json['search_results'] != null
          ? (json['search_results'] as List)
              .map((e) => SearchResult.fromJson(e))
              .toList()
          : null,
    );
  }
}

class ChatData {
  final String message;
  final String timestamp;
  final ChatMetadata? data;

  ChatData({
    required this.message,
    required this.timestamp,
    this.data,
  });

  factory ChatData.fromJson(Map<String, dynamic> json) {
    return ChatData(
      message: json['message'] ?? '',
      timestamp: json['timestamp'] ?? '',
      data: json['data'] != null
          ? ChatMetadata.fromJson(json['data'])
          : null,
    );
  }
}

class ChatMetadata {
  final int totalResults;
  final bool webSearchUsed;
  final List<String> suggestions;

  ChatMetadata({
    required this.totalResults,
    required this.webSearchUsed,
    required this.suggestions,
  });

  factory ChatMetadata.fromJson(Map<String, dynamic> json) {
    return ChatMetadata(
      totalResults: json['total_results'] ?? 0,
      webSearchUsed: json['web_search_used'] ?? false,
      suggestions: List<String>.from(json['suggestions'] ?? []),
    );
  }
}

class SearchResult {
  final String id;
  final BenefitMetadata metadata;
  final double similarityScore;
  final String searchType;

  SearchResult({
    required this.id,
    required this.metadata,
    required this.similarityScore,
    required this.searchType,
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      id: json['id'] ?? '',
      metadata: BenefitMetadata.fromJson(json['metadata'] ?? {}),
      similarityScore: (json['similarity_score'] ?? 0.0).toDouble(),
      searchType: json['search_type'] ?? 'unknown',
    );
  }
}

class BenefitMetadata {
  final String title;
  final String brand;
  final String category;
  final String benefitType;
  final String discountRate;
  final String conditions;
  final String validFrom;
  final String validTo;
  final String? url;

  BenefitMetadata({
    required this.title,
    required this.brand,
    required this.category,
    required this.benefitType,
    required this.discountRate,
    required this.conditions,
    required this.validFrom,
    required this.validTo,
    this.url,
  });

  factory BenefitMetadata.fromJson(Map<String, dynamic> json) {
    return BenefitMetadata(
      title: json['title'] ?? '',
      brand: json['brand'] ?? '',
      category: json['category'] ?? '',
      benefitType: json['benefit_type'] ?? '',
      discountRate: json['discount_rate'] ?? '',
      conditions: json['conditions'] ?? '',
      validFrom: json['valid_from'] ?? '',
      validTo: json['valid_to'] ?? '',
      url: json['url'],
    );
  }
}

// Flutter 클래스 정의는 API_SPEC_FLUTTER.md 파일을 참조하세요
```

### 4. 사용 예시

```dart
class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final BenefitsApiService _apiService = BenefitsApiService();
  final TextEditingController _controller = TextEditingController();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _checkServerHealth();
  }

  Future<void> _checkServerHealth() async {
    final isHealthy = await _apiService.checkHealth();
    if (!isHealthy) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('서버 연결 확인 중...')),
      );
    }
  }

  Future<void> _sendMessage() async {
    if (_controller.text.trim().isEmpty) return;

    final userMessage = _controller.text.trim();
    _controller.clear();

    setState(() {
      _messages.add(ChatMessage(text: userMessage, isUser: true));
      _isLoading = true;
    });

    try {
      final response = await _apiService.sendChatMessage(
        message: userMessage,
        userId: 'flutter_user_${DateTime.now().millisecondsSinceEpoch}',
      );

      if (response['success'] == true) {
        final botMessage = response['response']['message'];
        final suggestions = response['response']['data']['suggestions'] as List?;

        setState(() {
          _messages.add(ChatMessage(
            text: botMessage,
            isUser: false,
            suggestions: suggestions?.cast<String>(),
          ));
        });
      } else {
        _showError(response['error'] ?? '알 수 없는 오류');
      }
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  // 이미지 분석 기능 (상세 구현은 API_SPEC_FLUTTER.md 참조)
  Future<void> _analyzeImage() async {
    // 이미지 분석 로직 구현
    // 상세 코드는 API_SPEC_FLUTTER.md 파일을 참조하세요
  }

  void _showError(String error) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('오류: $error')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('혜택 추천 챗봇')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                return ChatBubble(message: _messages[index]);
              },
            ),
          ),
          if (_isLoading) const LinearProgressIndicator(),
          ChatInputField(
            controller: _controller,
            onSend: _sendMessage,
            onImagePick: _analyzeImage, // 이미지 분석 기능 추가
          ),
        ],
      ),
    );
  }
}

// 이미지 분석 기능이 포함된 채팅 입력 필드 (상세 구현은 API_SPEC_FLUTTER.md 참조)
            icon: const Icon(Icons.send, color: Colors.blue),
          ),
        ],
      ),
    );
  }
}
```

---

## 💻 예제 코드

### JavaScript/Node.js

```javascript
const axios = require('axios');

class BenefitsApiClient {
  constructor(baseUrl = 'http://your-server-ip') {
    this.baseUrl = baseUrl;
  }

  async sendChatMessage(message, userId, spendingHistory = []) {
    try {
      const response = await axios.post(`${this.baseUrl}/api/chat`, {
        message,
        user_id: userId,
        user_context: {
          spending_history: spendingHistory
        }
      });
      return response.data;
    } catch (error) {
      throw new Error(`API 요청 실패: ${error.message}`);
    }
  }

  async searchBenefits(query, userHistory = null, topK = 5) {
    try {
      const response = await axios.post(`${this.baseUrl}/api/search`, {
        query,
        user_history: userHistory,
        top_k: topK,
        debug: false
      });
      return response.data;
    } catch (error) {
      throw new Error(`검색 실패: ${error.message}`);
    }
  }

  async checkHealth() {
    try {
      const response = await axios.get(`${this.baseUrl}/health`);
      return response.data;
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  }
}

// 사용 예시
const client = new BenefitsApiClient();

async function example() {
  // 헬스체크
  const health = await client.checkHealth();
  console.log('서버 상태:', health.status);

  // 챗봇 메시지 전송
  const chatResponse = await client.sendChatMessage(
    '스타벅스 혜택 알려주세요',
    'user_12345'
  );
  console.log('챗봇 응답:', chatResponse.response.message);

  // 혜택 검색
  const searchResponse = await client.searchBenefits('카페 할인');
  console.log('검색 결과 수:', searchResponse.total_found);
}

example().catch(console.error);
```

### Python

```python
import requests
import json
from typing import Dict, List, Optional

class BenefitsApiClient:
    def __init__(self, base_url: str = "http://your-server-ip"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def send_chat_message(self, message: str, user_id: str, 
                         spending_history: List[Dict] = None) -> Dict:
        """챗봇 메시지 전송"""
        url = f"{self.base_url}/api/chat"
        data = {
            "message": message,
            "user_id": user_id,
            "user_context": {
                "spending_history": spending_history or []
            }
        }
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 요청 실패: {e}")

    def search_benefits(self, query: str, user_history: Dict = None, 
                       top_k: int = 5) -> Dict:
        """혜택 검색"""
        url = f"{self.base_url}/api/search"
        data = {
            "query": query,
            "user_history": user_history,
            "top_k": top_k,
            "debug": False
        }
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"검색 실패: {e}")

    def check_health(self) -> Dict:
        """헬스체크"""
        url = f"{self.base_url}/health"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "unhealthy", "error": str(e)}

    def get_categories(self) -> List[str]:
        """카테고리 목록 조회"""
        url = f"{self.base_url}/api/categories"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("categories", [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"카테고리 조회 실패: {e}")

    def analyze_image(self, image_path: str, debug: bool = False) -> Dict:
        """이미지 OCR 분석 및 브랜드 매칭"""
        # 이미지 분석 로직 구현
        # 상세 코드는 API_SPEC_FLUTTER.md 파일을 참조하세요
        pass

# 사용 예시
def main():
    client = BenefitsApiClient()
    
    # 헬스체크
    health = client.check_health()
    print(f"서버 상태: {health['status']}")
    
    # 챗봇 메시지 전송
    chat_response = client.send_chat_message(
        "스타벅스 혜택 알려주세요",
        "user_12345"
    )
    print(f"챗봇 응답: {chat_response['response']['message']}")
    
    # 혜택 검색
    search_response = client.search_benefits("카페 할인")
    print(f"검색 결과 수: {search_response['total_found']}")
    
    # 카테고리 목록
    categories = client.get_categories()
    print(f"지원 카테고리: {categories}")
    
    # 이미지 OCR 분석 (상세 구현은 API_SPEC_FLUTTER.md 참조)
    # client.analyze_image("receipt.jpg", debug=True)

if __name__ == "__main__":
    main()
```

### cURL 예제

```bash
#!/bin/bash

# 서버 정보
BASE_URL="http://your-server-ip"

# 헬스체크
echo "=== 헬스체크 ==="
curl -X GET "${BASE_URL}/health" \
  -H "Accept: application/json" \
  | jq '.'

# 챗봇 메시지 전송
echo -e "\n=== 챗봇 메시지 전송 ==="
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "스타벅스 혜택 알려주세요",
    "user_id": "curl_user_12345",
    "user_context": {
      "spending_history": [
        {
          "brand": "스타벅스",
          "category": "카페",
          "amount": 5000,
          "date": "2024-01-15"
        }
      ]
    }
  }' \
  | jq '.'

# 혜택 검색
echo -e "\n=== 혜택 검색 ==="
curl -X POST "${BASE_URL}/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "카페 할인",
    "user_history": {
      "preferred_brands": ["스타벅스", "이디야"],
      "preferred_categories": ["카페"]
    },
    "top_k": 5,
    "debug": false
  }' \
  | jq '.'

# 카테고리 목록 조회
echo -e "\n=== 카테고리 목록 ==="
curl -X GET "${BASE_URL}/api/categories" \
  -H "Accept: application/json" \
  | jq '.'

# 이미지 OCR 분석 (상세 구현은 API_SPEC_FLUTTER.md 참조)
# curl -X POST "${BASE_URL}/api/analyze-image" \
#   -F "image=@receipt.jpg" \
#   -F "debug=true" \
#   | jq '.'
```

---

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. 서버 연결 실패

**증상**: `Connection refused` 또는 `timeout` 오류

**해결 방법**:
```bash
# 서버 상태 확인
curl -X GET http://your-server-ip/health

# 방화벽 확인
sudo ufw status

# 포트 확인
sudo netstat -tlnp | grep :5000
```

#### 2. 502 Bad Gateway

**증상**: Nginx에서 502 오류 반환

**해결 방법**:
```bash
# 애플리케이션 상태 확인
sudo systemctl status benefits-api

# 로그 확인
sudo journalctl -u benefits-api -f

# 애플리케이션 재시작
sudo systemctl restart benefits-api
```

#### 3. 메모리 부족

**증상**: 서버 응답 지연 또는 오류

**해결 방법**:
```bash
# 메모리 사용량 확인
free -h

# 프로세스별 메모리 사용량
ps aux --sort=-%mem | head

# 스왑 파일 생성
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. API 키 오류

**증상**: AI 서비스 관련 오류

**해결 방법**:
```bash
# 환경 변수 확인
sudo -u benefits /opt/benefits-api/venv/bin/python -c "
import os
print('CLOVA_STUDIO_API_KEY:', os.environ.get('CLOVA_STUDIO_API_KEY'))
"

# 환경 변수 재설정
sudo nano /opt/benefits-api/app/.env
sudo systemctl restart benefits-api
```

### 성능 최적화

#### 1. 연결 풀링

```dart
// Flutter에서 HTTP 클라이언트 재사용
class ApiClient {
  static final http.Client _client = http.Client();
  
  static http.Client get client => _client;
}
```

#### 2. 캐싱 전략

```dart
// 카테고리 목록 캐싱
class CategoryCache {
  static List<String>? _cachedCategories;
  static DateTime? _lastUpdate;
  
  static Future<List<String>> getCategories() async {
    if (_cachedCategories != null && 
        _lastUpdate != null && 
        DateTime.now().difference(_lastUpdate!).inMinutes < 60) {
      return _cachedCategories!;
    }
    
    final categories = await apiService.getCategories();
    _cachedCategories = categories;
    _lastUpdate = DateTime.now();
    return categories;
  }
}
```

#### 3. 타임아웃 설정

```dart
// 적절한 타임아웃 설정
final response = await http.post(
  url,
  headers: headers,
  body: body,
).timeout(const Duration(seconds: 30));
```

### 디버깅 팁

#### 1. 로그 확인

```bash
# 실시간 로그 모니터링
sudo journalctl -u benefits-api -f

# 특정 시간대 로그
sudo journalctl -u benefits-api --since "2024-01-20 10:00:00"

# 에러 로그만 확인
sudo journalctl -u benefits-api -p err
```

#### 2. API 테스트

```bash
# 간단한 헬스체크
curl -v http://your-server-ip/health

# 상세한 요청 정보
curl -v -X POST http://your-server-ip/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "user_id": "test"}' \
  -w "\n시간: %{time_total}s\n상태: %{http_code}\n"
```

#### 3. 네트워크 진단

```bash
# 포트 스캔
nmap -p 80,443,5000 your-server-ip

# 연결 테스트
telnet your-server-ip 80

# DNS 확인
nslookup your-server-ip
```

---

## 📞 지원 및 문의

### 기술 지원
- **이슈 리포팅**: GitHub Issues
- **문서**: [API 문서](http://your-server/api/info)
- **헬스체크**: [http://your-server/health](http://your-server/health)

### 연락처
- **이메일**: support@example.com
- **문서**: [API 가이드](https://github.com/your-repo/api-docs)

### 버전 정보
- **현재 버전**: 2.1.0-ec2
- **최종 업데이트**: 2024년 1월
- **플랫폼**: AWS EC2 + Ubuntu

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**🎯 이 문서는 혜택 추천 챗봇 API의 완전한 사용 가이드를 제공합니다.**
**📱 Flutter 개발자를 위한 상세한 통합 가이드가 포함되어 있습니다.**
**🔧 문제 해결 및 성능 최적화 팁을 통해 안정적인 서비스 구축을 도와줍니다.** 