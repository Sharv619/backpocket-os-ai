package com.backpocket.os

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.util.Locale
import java.util.UUID

class MainActivity : FlutterActivity(),
    MethodChannel.MethodCallHandler,
    EventChannel.StreamHandler,
    TextToSpeech.OnInitListener {
    private val channelName = "backpocket/ai_edge"
    private val eventChannelName = "backpocket/ai_edge/events"
    private lateinit var localIntentEngine: LocalIntentEngine
    private val activityScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val mainHandler = Handler(Looper.getMainLooper())

    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var pendingSpeechResult: MethodChannel.Result? = null
    private var inferenceEventSink: EventChannel.EventSink? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        localIntentEngine = LocalIntentEngine(this)
        ensureTextToSpeech()
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName)
            .setMethodCallHandler(this)
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, eventChannelName)
            .setStreamHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "getCapabilities" -> launchMethod(result) { getCapabilities() }

            "ensureModelInstalled" -> {
                val modelId = call.argument<String>("model_id") ?: DEFAULT_MODEL_ID
                launchMethod(result) {
                    localIntentEngine.ensureModelInstalled(modelId)
                }
            }

            "importModelFromPath" -> {
                val modelId = call.argument<String>("model_id") ?: DEFAULT_MODEL_ID
                val sourcePath = call.argument<String>("source_path").orEmpty()
                launchMethod(result) {
                    localIntentEngine.importModelFromPath(
                        modelId = modelId,
                        sourcePath = sourcePath,
                    )
                }
            }

            "runIntentPipeline" -> {
                @Suppress("UNCHECKED_CAST")
                val metadata = call.argument<Map<String, Any?>>("metadata") ?: emptyMap()
                val transcript = call.argument<String>("transcript").orEmpty()
                val screenContext = call.argument<String>("screen_context") ?: "dashboard"
                val sessionId = call.argument<String>("session_id")
                val requestId = call.argument<String>("request_id") ?: UUID.randomUUID().toString()

                launchMethod(result) {
                    val response = localIntentEngine.process(
                        transcript = transcript,
                        screenContext = screenContext,
                        sessionId = sessionId,
                        metadata = metadata,
                        requestId = requestId,
                    ) { event ->
                        emitInferenceEvent(
                            requestId = requestId,
                            payload = event,
                        )
                    }
                    response + mapOf(
                        "request_id" to requestId,
                        "runtime_mode" to localIntentEngine.runtimeMode(),
                    )
                }
            }

            "recognizeOfflineSpeech" -> recognizeOfflineSpeech(call, result)

            "speakOffline" -> {
                val text = call.argument<String>("text").orEmpty()
                result.success(speakOffline(text))
            }

            else -> result.notImplemented()
        }
    }

    override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
        inferenceEventSink = events
    }

    override fun onCancel(arguments: Any?) {
        inferenceEventSink = null
    }

    private fun launchMethod(
        result: MethodChannel.Result,
        block: suspend () -> Any?,
    ) {
        activityScope.launch {
            try {
                result.success(block())
            } catch (t: Throwable) {
                result.error(
                    "ai_edge_error",
                    t.message ?: t::class.java.simpleName,
                    null,
                )
            }
        }
    }

    private fun getCapabilities(): Map<String, Any?> {
        val model = localIntentEngine.inspectModel(DEFAULT_MODEL_ID)
        return mapOf(
            "supported_platform" to true,
            "native_bridge_available" to true,
            "local_tts_available" to ttsReady,
            "offline_speech_available" to SpeechRecognizer.isRecognitionAvailable(this),
            "litertlm_library_present" to localIntentEngine.isLiteRtLmAvailable(),
            "model_status" to model["status"],
            "model_path" to model["local_path"],
            "model_message" to model["message"],
            "discovered_source_path" to model["discovered_source_path"],
            "sdk_version" to localIntentEngine.liteRtLmSdkVersion(),
            "runtime_mode" to localIntentEngine.runtimeMode(),
            "supported_intents" to localIntentEngine.supportedIntents(),
        )
    }

    private fun recognizeOfflineSpeech(call: MethodCall, result: MethodChannel.Result) {
        if (pendingSpeechResult != null) {
            result.success(mapOf("error" to "Speech recognition already in progress."))
            return
        }
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            result.success(mapOf("error" to "Speech recognizer unavailable on this device."))
            return
        }

        val prompt = call.argument<String>("prompt").orEmpty()
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
            if (prompt.isNotBlank()) {
                putExtra(RecognizerIntent.EXTRA_PROMPT, prompt)
            }
        }
        pendingSpeechResult = result
        @Suppress("DEPRECATION")
        startActivityForResult(intent, OFFLINE_SPEECH_REQUEST_CODE)
    }

    @Deprecated("Handled for FlutterActivity compatibility")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != OFFLINE_SPEECH_REQUEST_CODE) {
            return
        }

        val callback = pendingSpeechResult ?: return
        val transcript = if (resultCode == RESULT_OK) {
            data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
        } else {
            null
        }
        callback.success(
            if (transcript.isNullOrBlank()) {
                mapOf("error" to "No offline transcript returned.")
            } else {
                mapOf("transcript" to transcript)
            },
        )
        pendingSpeechResult = null
    }

    private fun ensureTextToSpeech() {
        if (tts == null) {
            tts = TextToSpeech(applicationContext, this)
        }
    }

    private fun speakOffline(text: String): Boolean {
        if (text.isBlank()) return false
        ensureTextToSpeech()
        if (!ttsReady) return false
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "backpocket-offline")
        return true
    }

    override fun onInit(status: Int) {
        ttsReady = status == TextToSpeech.SUCCESS
        if (ttsReady) {
            tts?.language = Locale.US
        }
    }

    private fun emitInferenceEvent(
        requestId: String,
        payload: Map<String, Any?>,
    ) {
        val sink = inferenceEventSink ?: return
        val event = mapOf("request_id" to requestId) + payload
        mainHandler.post {
            sink.success(event)
        }
    }

    override fun onDestroy() {
        activityScope.cancel()
        localIntentEngine.close()
        tts?.stop()
        tts?.shutdown()
        super.onDestroy()
    }

    companion object {
        private const val DEFAULT_MODEL_ID = "gemma-3n-e2b-it"
        private const val OFFLINE_SPEECH_REQUEST_CODE = 44102
    }
}
