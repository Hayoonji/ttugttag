# 🚀 혜택 추천 챗봇 API 명세서 (Flutter용)

## 📋 기본 정보

- **Base URL**: `http://your-server-ip` 또는 `https://your-domain.com`
- **API Version**: 2.1.0-ec2
- **Content-Type**: `application/json`
- **Authentication**: 없음 (현재 버전)

## 🎯 주요 엔드포인트 (Flutter 권장)

### 1. 챗봇 메시지 전송 ⭐ **[추천]**

**플러터에서 가장 많이 사용할 API**

```http
POST /api/chat
```

#### 요청 (Request)

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

#### 응답 (Response)

```json
{
  "success": true,
  "response": {
    "message": "스타벅스 관련 혜택을 찾았습니다! 🎉\n\n1. **스타벅스 사이렌오더** - 별 적립 혜택...",
    "timestamp": "2024-01-20T10:30:00Z",
    "data": {
      "total_results": 5,
      "web_search_used": false,
      "search_strategy": {
        "categories_found": ["카페"],
        "brands_found": ["스타벅스"]
      },
      "suggestions": ["이디야 혜택도 알려주세요", "카페 할인카드 추천해주세요"]
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

#### Flutter 구현 예시

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:flutter/material.dart';

class ChatService {
  static const String baseUrl = 'http://your-server-ip';

  Future<ChatResponse> sendMessage(String message, String userId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/chat'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'message': message,
        'user_id': userId,
        'user_context': {'spending_history': []}
      }),
    );

    if (response.statusCode == 200) {
      return ChatResponse.fromJson(json.decode(response.body));
    } else {
      throw Exception('챗봇 요청 실패: ${response.statusCode}');
    }
  }
}
```

---

### 2. 혜택 검색 API

```http
POST /api/search
```

#### 요청

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

#### 응답

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

---

### 3. AI 개인화 추천

```http
POST /api/recommend
```

#### 요청

```json
{
  "query": "맞춤 혜택 추천",
  "user_profile": {
    "preferred_brands": ["스타벅스", "맥도날드"],
    "preferred_categories": ["카페", "패스트푸드"],
    "total_transactions": 50,
    "average_spending": { "카페": 4500, "패스트푸드": 8000 }
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

#### 응답

```json
{
  "success": true,
  "query": "맞춤 혜택 추천",
  "ai_response": "고객님의 소비 패턴을 분석한 결과...",
  "search_results": [...],
  "user_profile_summary": {
    "total_transactions": 50,
    "preferred_brands": ["스타벅스", "맥도날드"],
    "profile_strength": "strong"
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

---

### 4. 헬스체크 API

```http
GET /health
```

#### 응답

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

---

### 5. 카테고리 목록 조회

```http
GET /api/categories
```

#### 응답

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

### 6. 이미지 OCR 분석 및 브랜드 매칭 ⭐ **[신규]**

이미지를 업로드하면 Clova OCR로 텍스트를 추출하고, 해당 날짜의 챗봇 대화 데이터와 매칭하여 브랜드를 찾는 API입니다.

```http
POST /api/analyze-image
```

#### 특징
- 이미지에서 텍스트 및 날짜 자동 추출
- 해당 날짜의 챗봇 대화 데이터와 브랜드 매칭
- Clova X AI를 활용한 지능형 브랜드 분석
- 다양한 이미지 형식 지원 (JPEG, PNG, BMP)

#### 요청 (multipart/form-data)

```dart
// Flutter 예시
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:flutter/material.dart';

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

#### 응답

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

  // 이미지 OCR 분석
  Future<Map<String, dynamic>> analyzeImage({
    required File imageFile,
    bool debug = false,
  }) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/analyze-image'),
    );
    
    request.files.add(
      await http.MultipartFile.fromPath('image', imageFile.path),
    );
    request.fields['debug'] = debug.toString();
    
    try {
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw ApiException('이미지 분석 실패: ${response.statusCode}');
      }
    } catch (e) {
      throw ApiException('이미지 분석 중 오류: $e');
    }
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

class ImageAnalysisResponse {
  final bool success;
  final ImageAnalysisData? data;
  final String? message;
  final String? error;

  ImageAnalysisResponse({
    required this.success,
    this.data,
    this.message,
    this.error,
  });

  factory ImageAnalysisResponse.fromJson(Map<String, dynamic> json) {
    return ImageAnalysisResponse(
      success: json['success'] ?? false,
      data: json['data'] != null
          ? ImageAnalysisData.fromJson(json['data'])
          : null,
      message: json['message'],
      error: json['error'],
    );
  }
}

class ImageAnalysisData {
  final String extractedText;
  final String extractedDate;
  final List<String> matchedBrands;
  final Map<String, double> confidenceScores;
  final String analysisSummary;

  ImageAnalysisData({
    required this.extractedText,
    required this.extractedDate,
    required this.matchedBrands,
    required this.confidenceScores,
    required this.analysisSummary,
  });

  factory ImageAnalysisData.fromJson(Map<String, dynamic> json) {
    return ImageAnalysisData(
      extractedText: json['extracted_text'] ?? '',
      extractedDate: json['extracted_date'] ?? '',
      matchedBrands: List<String>.from(json['matched_brands'] ?? []),
      confidenceScores: Map<String, double>.from(
        json['confidence_scores'] ?? {},
      ),
      analysisSummary: json['analysis_summary'] ?? '',
    );
  }
}
```

### 4. 사용 예시

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:flutter/material.dart';

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

  // 이미지 분석 기능
  Future<void> _analyzeImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);
    
    if (image == null) return;
    
    setState(() {
      _isLoading = true;
    });
    
    try {
      final response = await _apiService.analyzeImage(
        imageFile: File(image.path),
        debug: true,
      );
      
      if (response['success'] == true) {
        final data = response['data'];
        final extractedText = data['extracted_text'];
        final matchedBrands = data['matched_brands'];
        final summary = data['analysis_summary'];
        
        final botMessage = '''
🔍 이미지 분석 완료!

📝 추출된 텍스트: $extractedText
📅 날짜: ${data['extracted_date']}
🏷️ 매칭된 브랜드: ${matchedBrands.join(', ')}
📊 분석 요약: $summary
        '''.trim();
        
        setState(() {
          _messages.add(ChatMessage(
            text: botMessage,
            isUser: false,
          ));
        });
      } else {
        _showError(response['error'] ?? '이미지 분석 실패');
      }
    } catch (e) {
      _showError('이미지 분석 중 오류: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
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

// 이미지 분석 기능이 포함된 채팅 입력 필드
class ChatInputField extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  final VoidCallback onImagePick;

  const ChatInputField({
    required this.controller,
    required this.onSend,
    required this.onImagePick,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey.shade300)),
      ),
      child: Row(
        children: [
          // 이미지 선택 버튼
          IconButton(
            onPressed: onImagePick,
            icon: const Icon(Icons.image, color: Colors.blue),
            tooltip: '이미지 분석',
          ),
          // 텍스트 입력 필드
          Expanded(
            child: TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: '메시지를 입력하거나 이미지를 선택하세요...',
                border: InputBorder.none,
              ),
              maxLines: null,
            ),
          ),
          // 전송 버튼
          IconButton(
            onPressed: onSend,
            icon: const Icon(Icons.send, color: Colors.blue),
          ),
        ],
      ),
    );
  }
}
```

## 🚨 에러 처리

### 공통 에러 응답 형식

```json
{
  "success": false,
  "error": "오류 메시지",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### HTTP 상태 코드

- `200`: 성공
- `400`: 잘못된 요청 (필수 파라미터 누락 등)
- `500`: 서버 내부 오류
- `503`: 서비스 사용 불가 (RAG 시스템 초기화 실패 등)

## 📊 성능 최적화 팁

1. **연결 재사용**: HTTP 클라이언트 인스턴스 재사용
2. **타임아웃 설정**: 네트워크 요청 타임아웃 적절히 설정
3. **캐싱**: 카테고리 목록 등 정적 데이터 로컬 캐싱
4. **배치 요청**: 여러 검색어는 한 번에 처리

## 🔐 보안 고려사항

1. **HTTPS 사용**: 프로덕션에서는 HTTPS 필수
2. **사용자 ID**: 개인정보가 포함되지 않은 고유 ID 사용
3. **입력 검증**: 클라이언트에서도 입력값 검증
4. **민감정보**: API 키 등은 환경변수로 관리

이 명세서를 참고하여 Flutter 앱에서 쉽게 연동하실 수 있습니다! 🚀
