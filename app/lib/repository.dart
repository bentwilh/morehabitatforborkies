import 'package:dio/dio.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

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
  static const String _endpoint = 'https://your.api/endpoint';

  final Dio _dio;
  ForestDataRepository({Dio? dio}) : _dio = dio ?? Dio();
  Future<List<ForestChangeData>> getForestChangeData(
      LatLng coords,
      DateTime startDate,
      DateTime endDate,
      ) async {
    try {
      final response = await _dio.post(
        _endpoint,
        data: {
          'latitude': coords.latitude,
          'longitude': coords.longitude,
          'startDate': startDate.toIso8601String(),
          'endDate': endDate.toIso8601String()
        },
      );
      if (response.statusCode == 200) {
        List<dynamic> dataList = response.data;
        return dataList.map((dataJson) => ForestChangeData.fromJson(dataJson)).toList();
      } else {
        throw Exception('Failed to load forest change data');
      }
    } on DioError catch (e) {
      // Handle DioError, including timeout, no internet, etc.
      print('DioError: $e');
      throw e;
    }
  }
}