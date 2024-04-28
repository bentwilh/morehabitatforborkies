class Incident {
  final String title;
  final DateTime timestamp;
  final String content;
  Incident({required this.title, required this.timestamp, required this.content});

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'timestamp': timestamp.toIso8601String(),
      'content': content,
    };
  }

  factory Incident.fromJson(Map<String, dynamic> json) {
    return Incident(
      title: json['title'],
      timestamp: DateTime.parse(json['timestamp']),
      content: json['content'],
    );
  }
}
