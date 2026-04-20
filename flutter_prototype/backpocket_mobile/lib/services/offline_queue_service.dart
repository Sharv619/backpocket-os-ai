import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

class OfflineQueueService {
  static final OfflineQueueService _instance = OfflineQueueService._internal();
  factory OfflineQueueService() => _instance;
  OfflineQueueService._internal();

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'offline_queue.db');

    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE voice_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transcript TEXT NOT NULL,
            screen_context TEXT NOT NULL,
            session_id TEXT,
            metadata TEXT,
            audio_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
        ''');
      },
    );
  }

  Future<int> queueVoiceCommand({
    required String transcript,
    required String screenContext,
    String? sessionId,
    Map<String, dynamic>? metadata,
    String? audioPath,
  }) async {
    final db = await database;
    return await db.insert('voice_commands', {
      'transcript': transcript,
      'screen_context': screenContext,
      'session_id': sessionId,
      'metadata': metadata != null ? jsonEncode(metadata) : null,
      'audio_path': audioPath,
    });
  }

  Future<List<Map<String, dynamic>>> getQueuedCommands() async {
    final db = await database;
    return await db.query('voice_commands', orderBy: 'created_at ASC');
  }

  Future<void> removeCommand(int id) async {
    final db = await database;
    await db.delete('voice_commands', where: 'id = ?', whereArgs: [id]);
  }

  Future<bool> hasInternet() async {
    final connectivityResult = await (Connectivity().checkConnectivity());
    return !connectivityResult.contains(ConnectivityResult.none);
  }
}
