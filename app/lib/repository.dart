import 'dart:convert';

import 'package:dio/dio.dart';

class ForestChangeData {
  final DateTime captureDate;
  final String captureImage;
  final String diffOverlay;
  final int vitalityScore;
  ForestChangeData({
    required this.captureDate,
    required this.captureImage,
    required this.diffOverlay,
    required this.vitalityScore,
  });
  factory ForestChangeData.fromJson(Map<String, dynamic> json) {
    return ForestChangeData(
      captureDate: DateTime.parse(json['captureDate']),
      captureImage: json['captureImage'],
      diffOverlay: json['diffOverlay'],
      vitalityScore: json['vitalityScore'],
    );
  }
}

class ForestDataRepository {
  static const String _endpoint = 'http://5.75.170.84/get-image';

  final Dio _dio;
  ForestDataRepository({Dio? dio}) : _dio = dio ?? Dio(BaseOptions(connectTimeout: Duration(seconds: 130),sendTimeout: Duration(seconds: 130),receiveTimeout: Duration(seconds: 130)));

  Future<bool> callNumber() async {
    return await _dio.get('https://morehabitatforborkies-production.up.railway.app/outboundCall').then((value) {
      if (200 == value.statusCode) {
        return true;
      }
      return false;
    },).onError((error, stackTrace) => false);
  }

  Future<Map<String, String>> getForestChangeData(
      ForestRequestDto request
      ) async {
    try {
      bool error = false;
      final response = await _dio.post(
        _endpoint,
        data: request.toJson(),
        options: Options(
          contentType: 'application/json'
        )
      ).onError((e, stackTrace) {
        error = true;
        print(e);
        return Response(requestOptions: RequestOptions());
      });
      if (error) {
        return {};
      }
      if (response.statusCode == 200) {
        Map<dynamic, dynamic> dataList = response.data;
        return dataList.map<String, String>((key, value) => MapEntry(key as String, value as String));
      } else {
        throw Exception('Failed to load forest change data');
      }
    } on DioError catch (e) {
      print('DioError: $e');
      throw e;
    }
  }
}

class ForestRequestDto {
  final double lat;
  final double lon;
  final int startYear;
  final int startMonth;
  final int endYear;
  final int endMonth;

  ForestRequestDto({
    required this.lat,
    required this.lon,
    required this.startYear,
    required this.startMonth,
    required this.endYear,
    required this.endMonth,
  });

  factory ForestRequestDto.fromRawJson(String str) => ForestRequestDto.fromJson(json.decode(str));

  String toRawJson() => json.encode(toJson());

  factory ForestRequestDto.fromJson(Map<String, dynamic> json) => ForestRequestDto(
    lat: json["lat"]?.toDouble(),
    lon: json["lon"]?.toDouble(),
    startYear: json["start_year"],
    startMonth: json["start_month"],
    endYear: json["end_year"],
    endMonth: json["end_month"],
  );

  Map<String, dynamic> toJson() => {
    "lat": lat,
    "lon": lon,
    "start_year": startYear,
    "start_month": startMonth,
    "end_year": endYear,
    "end_month": endMonth,
  };
}
