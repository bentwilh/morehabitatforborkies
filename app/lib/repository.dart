import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:tumai/IncidentEntry.dart';
import 'package:tumai/global.dart';
import 'package:tumai/incident.dart';

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
  ForestDataRepository({Dio? dio})
      : _dio = dio ??
            Dio(BaseOptions(
                connectTimeout: Duration(seconds: 130),
                sendTimeout: Duration(seconds: 130),
                receiveTimeout: Duration(seconds: 130)));

  Future<bool> callNumber() async {
    incidents.value = [...incidents.value]..add(Incident(
        title: "Original Report",
        timestamp: DateTime.now(),
        content: "Incident reported to local authority"));
    return await _dio
        .get(
            'https://morehabitatforborkies-production.up.railway.app/outboundCall')
        .then(
      (value) {
        if (200 == value.statusCode) {
          return true;
        }
        return false;
      },
    ).onError((error, stackTrace) => false);
  }


  Future<void> fetchIncidents() async {
    var data = await _dio
        .get(
            'https://morehabitatforborkies-production.up.railway.app/api/incidents')
        .then((value) {
      return (value.data as List<dynamic>)
          .map((e) => IncidentEntry.fromJson(e))
          .toList();
    });
    incidentEntries.value = data;
  }


  Future<void> removeIncidentEntry() async {
    
  }

  Future<void> addIncidentEntry(IncidentEntry entry) async {
    incidentEntries.value.add(entry);
    await _dio.post('https://morehabitatforborkies-production.up.railway.app/api/incidents', data: entry.toJson());
  }

  Future<void> fetchCalls() async {
    if (incidents.value.length == 2) {
      return;
    }
    var data = await _dio.get('https://morehabitatforborkies-production.up.railway.app/api/calls');
    /*
    new_record = {
        'record_id': record_id,
        'timestamp': datetime.now(),
        'caller_id': record_data.get('caller_id', 'Unknown'),
        'speech_text': record_data.get('speech_text', '')
    }
     */
    incidents.value = [Incident(timestamp: DateTime.now(), content: (data as Map<String, dynamic>)['speech_text'], title: 'Callback'), ...incidents.value];
  }

  Future<Map<String, String>> getForestChangeData(
      ForestRequestDto request) async {
    try {
      bool error = false;
      final response = await _dio
          .post(_endpoint,
              data: request.toJson(),
              options: Options(contentType: 'application/json'))
          .onError((e, stackTrace) {
        error = true;
        print(e);
        return Response(requestOptions: RequestOptions());
      });
      if (error) {
        return {};
      }
      if (response.statusCode == 200) {
        Map<dynamic, dynamic> dataList = response.data;
        return dataList.map<String, String>(
            (key, value) => MapEntry(key as String, value as String));
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

  factory ForestRequestDto.fromRawJson(String str) =>
      ForestRequestDto.fromJson(json.decode(str));

  String toRawJson() => json.encode(toJson());

  factory ForestRequestDto.fromJson(Map<String, dynamic> json) =>
      ForestRequestDto(
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
