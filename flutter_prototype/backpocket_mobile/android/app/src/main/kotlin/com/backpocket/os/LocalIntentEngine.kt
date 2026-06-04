package com.backpocket.os

import android.content.Context
import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.ConversationConfig
import com.google.ai.edge.litertlm.Contents
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import com.google.ai.edge.litertlm.ExperimentalApi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.Locale
import java.util.UUID
import kotlin.math.roundToInt

private const val LITERT_LM_SDK_VERSION = "0.12.0"
private const val DEFAULT_MODEL_ID = "gemma-3n-e2b-it"
private const val DEFAULT_MODEL_FILE_NAME = "model.litertlm"

internal class LocalIntentEngine(
    private val context: Context,
) {
    private data class IntentConfig(
        val order: List<String>,
        val defaults: Map<String, Any?>,
        val questions: Map<String, String>,
    )

    private data class OfflineSession(
        val sessionId: String,
        var state: String = "IDLE",
        var intent: String? = null,
        var screenContext: String = "dashboard",
        var metadata: MutableMap<String, Any?> = mutableMapOf(),
        val collectedParams: MutableMap<String, Any?> = mutableMapOf(),
        val missingParams: MutableList<String> = mutableListOf(),
        var nextQuestion: String? = null,
    ) {
        fun reset() {
            state = "IDLE"
            intent = null
            collectedParams.clear()
            missingParams.clear()
            nextQuestion = null
        }

        fun toMap(): Map<String, Any?> = mapOf(
            "session_id" to sessionId,
            "state" to state,
            "intent" to intent,
            "collected_params" to collectedParams.toMap(),
            "missing_params" to missingParams.toList(),
            "next_question" to nextQuestion,
            "defaults" to emptyMap<String, Any?>(),
            "ttl" to 300,
        )
    }

    private data class ModelIntentResult(
        val intent: String,
        val confidence: Double,
        val result: Map<String, Any?>,
    )

    private val sessions = mutableMapOf<String, OfflineSession>()
    private val modelRuntime = LocalModelInferenceEngine(context)

    private val intentConfigs = mapOf(
        "construction.lead.create" to IntentConfig(
            order = listOf("client_name", "job_type", "location", "estimated_budget"),
            defaults = mapOf("urgency" to "medium", "email" to ""),
            questions = mapOf(
                "client_name" to "What's the client's name?",
                "job_type" to "What kind of job is it?",
                "location" to "Where is the job?",
                "estimated_budget" to "What's the budget estimate?",
            ),
        ),
        "construction.quote.create" to IntentConfig(
            order = listOf("lead_id", "materials_cost", "labor_cost", "markup_percent"),
            defaults = mapOf("markup_percent" to 20),
            questions = mapOf(
                "lead_id" to "Which lead id is this quote for?",
                "materials_cost" to "What's the materials cost?",
                "labor_cost" to "What's the labour cost?",
                "markup_percent" to "What's the markup percentage?",
            ),
        ),
        "construction.payment.record" to IntentConfig(
            order = listOf("quote_id", "amount"),
            defaults = emptyMap(),
            questions = mapOf(
                "quote_id" to "Which quote id is this payment for?",
                "amount" to "How much was paid?",
            ),
        ),
        "construction.quote.followup" to IntentConfig(
            order = listOf("quote_id"),
            defaults = emptyMap(),
            questions = mapOf("quote_id" to "Which quote should I follow up on?"),
        ),
        "construction.quote.invoice" to IntentConfig(
            order = listOf("quote_id"),
            defaults = emptyMap(),
            questions = mapOf("quote_id" to "Which quote should I invoice?"),
        ),
    )

    fun supportedIntents(): List<String> = listOf(
        "navigate.screen",
        "dashboard.summary",
        "construction.lead.create",
        "construction.quote.create",
        "construction.payment.record",
        "construction.quote.followup",
        "construction.quote.invoice",
    )

    fun liteRtLmSdkVersion(): String = LITERT_LM_SDK_VERSION

    fun isLiteRtLmAvailable(): Boolean = runCatching {
        Class.forName("com.google.ai.edge.litertlm.Engine")
        true
    }.getOrDefault(false)

    suspend fun ensureModelInstalled(modelId: String): Map<String, Any?> {
        if (!isLiteRtLmAvailable()) {
            return unavailableModelStatus(
                modelId = modelId,
                message = "LiteRT-LM SDK classes are unavailable in this build.",
            )
        }

        val modelFile = modelSlotFile(modelId)
        modelFile.parentFile?.mkdirs()
        if (modelFile.exists()) {
            return mapOf(
                "model_id" to modelId,
                "status" to "downloaded_not_initialized",
                "local_path" to modelFile.absolutePath,
                "message" to "Model file is already in app storage. Runtime initialization is not automatic yet.",
                "sdk_version" to liteRtLmSdkVersion(),
            )
        }

        val discoveredSource = discoverSourceModelFile(modelId)
        if (discoveredSource != null) {
            return importModelFromFile(modelId, discoveredSource)
        }

        return mapOf(
            "model_id" to modelId,
            "status" to "manual_import_required",
            "local_path" to modelFile.absolutePath,
            "message" to "Model slot prepared at ${modelFile.absolutePath}. Use Import Model to select a .litertlm file.",
            "sdk_version" to liteRtLmSdkVersion(),
        )
    }

    suspend fun importModelFromPath(
        modelId: String,
        sourcePath: String,
    ): Map<String, Any?> {
        if (!isLiteRtLmAvailable()) {
            return unavailableModelStatus(
                modelId = modelId,
                message = "LiteRT-LM SDK classes are unavailable in this build.",
            )
        }
        if (sourcePath.isBlank()) {
            return mapOf(
                "model_id" to modelId,
                "status" to "import_failed",
                "local_path" to modelSlotFile(modelId).absolutePath,
                "message" to "No model file was selected.",
                "sdk_version" to liteRtLmSdkVersion(),
            )
        }

        val sourceFile = File(sourcePath)
        if (!sourceFile.exists() || !sourceFile.isFile) {
            return mapOf(
                "model_id" to modelId,
                "status" to "import_failed",
                "local_path" to modelSlotFile(modelId).absolutePath,
                "source_path" to sourcePath,
                "message" to "Selected model file is not readable from $sourcePath.",
                "sdk_version" to liteRtLmSdkVersion(),
            )
        }

        return importModelFromFile(modelId, sourceFile)
    }

    fun inspectModel(modelId: String): Map<String, Any?> {
        val modelFile = modelSlotFile(modelId)
        val discoveredSource = discoverSourceModelFile(modelId)
        val slotPrepared = modelFile.parentFile?.exists() == true

        val (status, message) = when {
            !isLiteRtLmAvailable() -> "sdk_missing" to
                "LiteRT-LM SDK classes are unavailable in this build."
            modelRuntime.isReadyFor(modelFile.absolutePath) -> "ready" to
                "LiteRT-LM model initialized locally."
            modelFile.exists() -> "downloaded_not_initialized" to
                "Model file is present but not initialized yet."
            discoveredSource != null -> "import_available" to
                "Found a candidate model file at ${discoveredSource.absolutePath}."
            slotPrepared -> "manual_import_required" to
                "Model slot prepared at ${modelFile.absolutePath}. Use Import Model to select a .litertlm file."
            else -> "missing" to
                "No local .litertlm model found yet. Import one from Settings."
        }

        return mapOf(
            "status" to status,
            "local_path" to modelFile.absolutePath,
            "message" to message,
            "discovered_source_path" to (discoveredSource?.absolutePath ?: ""),
            "sdk_version" to liteRtLmSdkVersion(),
        )
    }

    fun runtimeMode(): String = when {
        !isLiteRtLmAvailable() -> "sdk_missing"
        modelRuntime.isReady() -> "litertlm_streaming"
        else -> "heuristic_local_bridge"
    }

    private suspend fun importModelFromFile(
        modelId: String,
        sourceFile: File,
    ): Map<String, Any?> {
        val targetFile = modelSlotFile(modelId)
        return try {
            withContext(Dispatchers.IO) {
                targetFile.parentFile?.mkdirs()
                if (sourceFile.absolutePath != targetFile.absolutePath) {
                    val tempFile = File(targetFile.parentFile, "$DEFAULT_MODEL_FILE_NAME.tmp")
                    sourceFile.inputStream().use { input ->
                        tempFile.outputStream().use { output ->
                            input.copyTo(output)
                        }
                    }
                    if (targetFile.exists()) {
                        targetFile.delete()
                    }
                    if (!tempFile.renameTo(targetFile)) {
                        tempFile.copyTo(targetFile, overwrite = true)
                        tempFile.delete()
                    }
                }
            }
            mapOf(
                "model_id" to modelId,
                "status" to "downloaded_not_initialized",
                "local_path" to targetFile.absolutePath,
                "source_path" to sourceFile.absolutePath,
                "message" to "Model imported into app storage. Runtime initialization is not automatic yet.",
                "sdk_version" to liteRtLmSdkVersion(),
            )
        } catch (t: Throwable) {
            mapOf(
                "model_id" to modelId,
                "status" to "import_failed",
                "local_path" to targetFile.absolutePath,
                "source_path" to sourceFile.absolutePath,
                "message" to "Model import failed: ${t.message ?: t::class.java.simpleName}",
                "sdk_version" to liteRtLmSdkVersion(),
            )
        }
    }

    private suspend fun initializeModelStatus(
        modelId: String,
        modelFile: File,
        sourceFile: File? = null,
    ): Map<String, Any?> = try {
        modelRuntime.initializeModel(modelFile)
        mapOf(
            "model_id" to modelId,
            "status" to "ready",
            "local_path" to modelFile.absolutePath,
            "source_path" to (sourceFile?.absolutePath ?: ""),
            "message" to if (sourceFile != null && sourceFile.absolutePath != modelFile.absolutePath) {
                "Imported model from ${sourceFile.absolutePath} and initialized LiteRT-LM locally."
            } else {
                "LiteRT-LM model initialized locally."
            },
            "sdk_version" to liteRtLmSdkVersion(),
        )
    } catch (t: Throwable) {
        mapOf(
            "model_id" to modelId,
            "status" to "init_failed",
            "local_path" to modelFile.absolutePath,
            "source_path" to (sourceFile?.absolutePath ?: ""),
            "message" to "Model found but initialization failed: ${t.message ?: t::class.java.simpleName}",
            "sdk_version" to liteRtLmSdkVersion(),
        )
    }

    private fun unavailableModelStatus(
        modelId: String,
        message: String,
    ): Map<String, Any?> = mapOf(
        "model_id" to modelId,
        "status" to "sdk_missing",
        "local_path" to modelSlotFile(modelId).absolutePath,
        "message" to message,
        "sdk_version" to liteRtLmSdkVersion(),
    )

    private fun modelSlotFile(modelId: String): File =
        File(context.filesDir, "ai_models/$modelId/$DEFAULT_MODEL_FILE_NAME")

    private fun discoverSourceModelFile(modelId: String): File? {
        val candidateNames = linkedSetOf(
            DEFAULT_MODEL_FILE_NAME,
            "$modelId.litertlm",
            "$DEFAULT_MODEL_ID.litertlm",
        )
        val relativePaths = candidateNames.flatMap { fileName ->
            listOf(
                fileName,
                "ai_models/$modelId/$fileName",
                "models/$fileName",
                "Download/$fileName",
                "Documents/$fileName",
            )
        }
        val roots = listOfNotNull(
            context.filesDir,
            context.cacheDir,
            context.externalCacheDir,
            context.getExternalFilesDir(null),
            context.getExternalFilesDir("Download"),
            context.getExternalFilesDir("Documents"),
        )

        return roots.asSequence()
            .flatMap { root ->
                relativePaths.asSequence().map { relativePath -> File(root, relativePath) }
            }
            .firstOrNull { candidate ->
                candidate.exists() &&
                    candidate.isFile &&
                    candidate.extension.equals("litertlm", ignoreCase = true)
            }
    }

    suspend fun process(
        transcript: String,
        screenContext: String,
        sessionId: String?,
        metadata: Map<String, Any?>,
        requestId: String,
        onModelEvent: suspend (Map<String, Any?>) -> Unit = {},
    ): Map<String, Any?> {
        val normalized = transcript.trim()
        val resolvedSessionId = sessionId ?: UUID.randomUUID().toString()
        val session = sessions.getOrPut(resolvedSessionId) {
            OfflineSession(sessionId = resolvedSessionId)
        }
        session.screenContext = screenContext
        session.metadata = metadata.toMutableMap()

        if (normalized.isBlank()) {
            return unsupported(session, "Didn't catch that offline. Try again or type it.")
        }

        if (session.state == "IDLE" && modelRuntime.isReady()) {
            onModelEvent(
                mapOf(
                    "type" to "inference_started",
                    "runtime_mode" to runtimeMode(),
                    "transcript" to normalized,
                ),
            )
            val modelResult = runModelIntentExtraction(
                transcript = normalized,
                screenContext = screenContext,
                metadata = metadata,
                requestId = requestId,
                onModelEvent = onModelEvent,
            )
            if (modelResult != null) {
                return routeModelResult(session, modelResult, normalized)
            }
            onModelEvent(
                mapOf(
                    "type" to "inference_fallback",
                    "runtime_mode" to runtimeMode(),
                    "reason" to "model_output_unusable",
                ),
            )
        }

        return when (session.state) {
            "CONFIRMING" -> handleConfirmation(session, normalized)
            "COLLECTING" -> handleCollecting(session, normalized)
            else -> classifyAndRoute(session, normalized)
        }
    }

    suspend fun runLocalPrompt(
        prompt: String,
        requestId: String,
        onModelEvent: suspend (Map<String, Any?>) -> Unit = {},
    ): Map<String, Any?> {
        val normalized = prompt.trim()
        if (normalized.isBlank()) {
            return mapOf(
                "status" to "error",
                "response" to "",
                "message" to "Enter a prompt first.",
            )
        }
        if (!isLiteRtLmAvailable()) {
            return mapOf(
                "status" to "unavailable",
                "response" to "",
                "message" to "LiteRT-LM SDK classes are unavailable in this build.",
            )
        }

        val modelFile = modelSlotFile(DEFAULT_MODEL_ID)
        if (!modelRuntime.isReadyFor(modelFile.absolutePath)) {
            if (!modelFile.exists()) {
                return mapOf(
                    "status" to "model_missing",
                    "response" to "",
                    "message" to "Import a .litertlm model from Settings before using AI Edge Gallery mode.",
                    "model_path" to modelFile.absolutePath,
                )
            }

            val status = initializeModelStatus(DEFAULT_MODEL_ID, modelFile)
            if (status["status"] != "ready") {
                return mapOf(
                    "status" to "init_failed",
                    "response" to "",
                    "message" to (status["message"] ?: "Model initialization failed."),
                    "model_path" to modelFile.absolutePath,
                )
            }
        }

        return try {
            onModelEvent(
                mapOf(
                    "type" to "inference_started",
                    "runtime_mode" to runtimeMode(),
                    "transcript" to normalized,
                ),
            )
            val response = modelRuntime.runPrompt(
                userInput = normalized,
                onChunk = { chunk ->
                    onModelEvent(
                        mapOf(
                            "type" to "inference_chunk",
                            "runtime_mode" to runtimeMode(),
                            "chunk" to chunk,
                        ),
                    )
                },
            )
            onModelEvent(
                mapOf(
                    "type" to "inference_completed",
                    "runtime_mode" to runtimeMode(),
                ),
            )
            mapOf(
                "status" to "success",
                "response" to response,
                "message" to "",
                "model_path" to modelFile.absolutePath,
            )
        } catch (t: Throwable) {
            val message = t.message ?: t::class.java.simpleName
            onModelEvent(
                mapOf(
                    "type" to "inference_error",
                    "runtime_mode" to runtimeMode(),
                    "message" to message,
                ),
            )
            mapOf(
                "status" to "error",
                "response" to "",
                "message" to message,
                "model_path" to modelFile.absolutePath,
            )
        }
    }

    private fun classifyAndRoute(session: OfflineSession, transcript: String): Map<String, Any?> {
        val lower = transcript.lowercase()
        val intent = classifyIntent(lower)
            ?: return unsupported(
                session,
                "I can't do that offline yet. I can still handle leads, quotes, payments, follow-ups, invoices, and navigation.",
            )

        return when (intent) {
            "navigate.screen" -> navigateResponse(session, transcript)
            "dashboard.summary" -> dashboardResponse(session)
            else -> beginStructuredIntent(session, intent, transcript)
        }
    }

    private fun routeModelResult(
        session: OfflineSession,
        modelResult: ModelIntentResult,
        transcript: String,
    ): Map<String, Any?> {
        if (modelResult.confidence < 0.55 || !supportedIntents().contains(modelResult.intent)) {
            return classifyAndRoute(session, transcript)
        }

        return when (modelResult.intent) {
            "navigate.screen" -> navigateResponse(
                session = session,
                transcript = (modelResult.result["screen"] as? String) ?: transcript,
            )
            "dashboard.summary" -> dashboardResponse(session)
            else -> beginStructuredIntent(
                session = session,
                intent = modelResult.intent,
                transcript = transcript,
                seedParams = modelResult.result,
            )
        }
    }

    private fun beginStructuredIntent(
        session: OfflineSession,
        intent: String,
        transcript: String,
        seedParams: Map<String, Any?> = emptyMap(),
    ): Map<String, Any?> {
        val config = intentConfigs[intent]
            ?: return unsupported(session, "That offline flow is not configured yet.")

        session.reset()
        session.intent = intent
        session.state = "COLLECTING"

        val extracted = extractParams(intent, transcript, session.metadata) + seedParams
        val params = session.collectedParams
        params.putAll(extracted.filterValues { it != null })
        config.defaults.forEach { (key, value) ->
            if (!params.containsKey(key) && !config.order.contains(key)) {
                params[key] = value
            }
        }

        session.missingParams.clear()
        session.missingParams.addAll(
            config.order.filter { key ->
                val value = params[key]
                value == null || (value is String && value.isBlank())
            },
        )

        if (session.missingParams.isEmpty()) {
            return confirmStructuredIntent(session)
        }

        val next = session.missingParams.first()
        session.nextQuestion = config.questions[next]
        return response(
            session = session,
            intent = intent,
            action = "collect",
            speech = session.nextQuestion ?: "Need one more detail.",
            result = mapOf("mode" to "offline_local", "sync_status" to "none") + params,
            followUpPrompt = session.nextQuestion,
        )
    }

    private fun handleCollecting(session: OfflineSession, transcript: String): Map<String, Any?> {
        if (isNegative(transcript)) {
            session.reset()
            return response(
                session = session,
                intent = "meta.cancel",
                action = "execute",
                speech = "Cancelled.",
                result = mapOf("mode" to "offline_local", "sync_status" to "none"),
            )
        }

        val intent = session.intent ?: return unsupported(session, "Offline session expired. Start again.")
        val current = session.missingParams.firstOrNull() ?: return confirmStructuredIntent(session)
        val value = parseCollectedValue(intent, current, transcript, session.metadata)
        if (value == null || (value is String && value.isBlank())) {
            return response(
                session = session,
                intent = intent,
                action = "collect",
                speech = session.nextQuestion ?: "Need one more detail.",
                result = mapOf("mode" to "offline_local", "sync_status" to "none") + session.collectedParams,
                followUpPrompt = session.nextQuestion,
            )
        }

        session.collectedParams[current] = value
        session.missingParams.removeAt(0)
        if (session.missingParams.isEmpty()) {
            return confirmStructuredIntent(session)
        }

        val config = intentConfigs[intent]
        session.nextQuestion = config?.questions?.get(session.missingParams.first())
        return response(
            session = session,
            intent = intent,
            action = "collect",
            speech = session.nextQuestion ?: "Need one more detail.",
            result = mapOf("mode" to "offline_local", "sync_status" to "none") + session.collectedParams,
            followUpPrompt = session.nextQuestion,
        )
    }

    private fun confirmStructuredIntent(session: OfflineSession): Map<String, Any?> {
        session.state = "CONFIRMING"
        session.nextQuestion = null
        val intent = session.intent ?: "unknown"
        val params = session.collectedParams.toMap()
        return response(
            session = session,
            intent = intent,
            action = "confirm",
            speech = confirmationPrompt(intent, params),
            result = mapOf("mode" to "offline_local", "sync_status" to "none") + params,
            needsConfirmation = true,
        )
    }

    private fun handleConfirmation(session: OfflineSession, transcript: String): Map<String, Any?> {
        val intent = session.intent ?: return unsupported(session, "Offline session expired. Start again.")
        if (isNegative(transcript)) {
            session.reset()
            return response(
                session = session,
                intent = "meta.cancel",
                action = "execute",
                speech = "Cancelled.",
                result = mapOf("mode" to "offline_local", "sync_status" to "none"),
            )
        }
        if (!isPositive(transcript)) {
            return response(
                session = session,
                intent = intent,
                action = "confirm",
                speech = "Say yes to confirm or no to cancel.",
                result = mapOf("mode" to "offline_local", "sync_status" to "none") + session.collectedParams,
                needsConfirmation = true,
            )
        }

        val params = session.collectedParams.toMutableMap()
        session.reset()
        return executeIntent(session, intent, params)
    }

    private fun executeIntent(
        session: OfflineSession,
        intent: String,
        params: MutableMap<String, Any?>,
    ): Map<String, Any?> {
        val clientActionId = UUID.randomUUID().toString()
        return when (intent) {
            "construction.lead.create" -> {
                val syncPayload = mapOf(
                    "client_name" to (params["client_name"] ?: ""),
                    "email" to (params["email"] ?: ""),
                    "job_type" to (params["job_type"] ?: ""),
                    "location" to (params["location"] ?: ""),
                    "urgency" to (params["urgency"] ?: "medium"),
                    "estimated_budget" to params["estimated_budget"],
                )
                response(
                    session = session,
                    intent = intent,
                    action = "execute",
                    speech = "Lead saved locally. I'll sync ${params["client_name"] ?: "it"} when you're back online.",
                    result = syncResult(
                        clientActionId = clientActionId,
                        syncPayload = syncPayload,
                        extra = params,
                    ),
                    uiAction = mapOf("navigate_to" to "construction", "tab_index" to 0, "refresh_data" to true),
                )
            }

            "construction.quote.create" -> {
                val syncPayload = mapOf(
                    "lead_id" to params["lead_id"],
                    "materials_cost" to params["materials_cost"],
                    "labor_cost" to params["labor_cost"],
                    "markup_percent" to params["markup_percent"],
                )
                val total = ((params["materials_cost"] as? Double ?: 0.0) +
                    (params["labor_cost"] as? Double ?: 0.0)) *
                    (1 + ((params["markup_percent"] as? Int ?: 20) / 100.0))
                response(
                    session = session,
                    intent = intent,
                    action = "execute",
                    speech = "Quote saved locally at ${currency(total)}. I'll sync it when reception is back.",
                    result = syncResult(
                        clientActionId = clientActionId,
                        syncPayload = syncPayload,
                        extra = params + mapOf("total_amount" to total),
                    ),
                    uiAction = mapOf("navigate_to" to "construction", "tab_index" to 1, "refresh_data" to true),
                )
            }

            "construction.payment.record" -> {
                val syncPayload = mapOf(
                    "quote_id" to params["quote_id"],
                    "amount" to params["amount"],
                )
                response(
                    session = session,
                    intent = intent,
                    action = "execute",
                    speech = "Payment of ${currency(params["amount"] as? Double ?: 0.0)} saved locally for sync.",
                    result = syncResult(
                        clientActionId = clientActionId,
                        syncPayload = syncPayload,
                        extra = params,
                    ),
                    uiAction = mapOf("navigate_to" to "construction", "tab_index" to 2, "refresh_data" to true),
                )
            }

            "construction.quote.followup" -> {
                val quoteId = (params["quote_id"] as? Int) ?: 0
                val message = "Hi, just checking whether you had any questions about quote #$quoteId. Happy to run through it when you're ready."
                response(
                    session = session,
                    intent = intent,
                    action = "execute",
                    speech = "Here's the follow-up: $message",
                    result = mapOf(
                        "mode" to "offline_local",
                        "sync_status" to "local_only",
                        "sync_required" to false,
                        "client_action_id" to clientActionId,
                        "message" to message,
                        "quote_id" to quoteId,
                    ),
                    uiAction = mapOf("navigate_to" to "construction", "tab_index" to 1),
                )
            }

            "construction.quote.invoice" -> {
                val quoteId = (params["quote_id"] as? Int) ?: 0
                response(
                    session = session,
                    intent = intent,
                    action = "execute",
                    speech = "Invoice prep saved for quote #$quoteId. Generate the PDF once you're back online.",
                    result = mapOf(
                        "mode" to "offline_local",
                        "sync_status" to "local_only",
                        "sync_required" to false,
                        "client_action_id" to clientActionId,
                        "quote_id" to quoteId,
                    ),
                    uiAction = mapOf("navigate_to" to "construction", "tab_index" to 1),
                )
            }

            else -> unsupported(session, "That offline flow isn't executable yet.")
        }
    }

    private fun navigateResponse(session: OfflineSession, transcript: String): Map<String, Any?> {
        val target = when {
            transcript.contains("inbox", ignoreCase = true) -> "inbox"
            transcript.contains("construction", ignoreCase = true) || transcript.contains("jobs", ignoreCase = true) -> "construction"
            transcript.contains("settings", ignoreCase = true) -> "settings"
            transcript.contains("dashboard", ignoreCase = true) || transcript.contains("home", ignoreCase = true) -> "dashboard"
            else -> "dashboard"
        }
        session.reset()
        return response(
            session = session,
            intent = "navigate.screen",
            action = "navigate",
            speech = "",
            result = mapOf("mode" to "offline_local", "sync_status" to "none", "screen" to target),
            uiAction = mapOf("navigate_to" to target),
        )
    }

    private fun dashboardResponse(session: OfflineSession): Map<String, Any?> {
        session.reset()
        return response(
            session = session,
            intent = "dashboard.summary",
            action = "display",
            speech = "You're offline. I can still save leads, quotes, payments, follow-ups, and invoice prep locally.",
            result = mapOf("mode" to "offline_local", "sync_status" to "none"),
            uiAction = mapOf("navigate_to" to "dashboard"),
        )
    }

    private fun unsupported(session: OfflineSession, message: String): Map<String, Any?> {
        session.reset()
        return response(
            session = session,
            intent = "chat.ask",
            action = "clarify",
            speech = message,
            result = mapOf("mode" to "unsupported_offline", "sync_status" to "none", "error" to message),
        )
    }

    private fun syncResult(
        clientActionId: String,
        syncPayload: Map<String, Any?>,
        extra: Map<String, Any?>,
    ): Map<String, Any?> = mapOf(
        "mode" to "queued_for_sync",
        "sync_status" to "pending",
        "sync_required" to true,
        "client_action_id" to clientActionId,
        "sync_payload" to syncPayload,
    ) + extra

    private fun response(
        session: OfflineSession,
        intent: String,
        action: String,
        speech: String,
        result: Map<String, Any?>,
        needsConfirmation: Boolean = false,
        followUpPrompt: String? = null,
        uiAction: Map<String, Any?> = emptyMap(),
        confidence: Double = 0.92,
    ): Map<String, Any?> = mapOf(
        "intent" to intent,
        "confidence" to confidence,
        "action" to action,
        "result" to result,
        "speech_response" to speech,
        "ui_action" to uiAction,
        "needs_confirmation" to needsConfirmation,
        "follow_up_prompt" to followUpPrompt,
        "session_state" to session.toMap(),
    )

    private suspend fun runModelIntentExtraction(
        transcript: String,
        screenContext: String,
        metadata: Map<String, Any?>,
        requestId: String,
        onModelEvent: suspend (Map<String, Any?>) -> Unit,
    ): ModelIntentResult? {
        return try {
            val raw = modelRuntime.extractTradieIntent(
                userInput = transcript,
                screenContext = screenContext,
                metadata = metadata,
            ) { chunk ->
                onModelEvent(
                    mapOf(
                        "type" to "inference_chunk",
                        "runtime_mode" to runtimeMode(),
                        "chunk" to chunk,
                    ),
                )
            }
            onModelEvent(
                mapOf(
                    "type" to "inference_completed",
                    "runtime_mode" to runtimeMode(),
                    "request_id" to requestId,
                    "raw_response_chars" to raw.length,
                ),
            )
            parseModelIntent(raw)
        } catch (t: Throwable) {
            onModelEvent(
                mapOf(
                    "type" to "inference_error",
                    "runtime_mode" to runtimeMode(),
                    "request_id" to requestId,
                    "message" to (t.message ?: t::class.java.simpleName),
                ),
            )
            null
        }
    }

    private fun classifyIntent(lower: String): String? = when {
        (lower.contains("go to") || lower.startsWith("open ") || lower.startsWith("show ")) && (
            lower.contains("dashboard") || lower.contains("inbox") || lower.contains("construction") || lower.contains("settings")
        ) -> "navigate.screen"
        lower.contains("pipeline") || lower.contains("what's happening") || lower.contains("whats happening") -> "dashboard.summary"
        lower.contains("follow up") || lower.contains("followup") -> "construction.quote.followup"
        lower.contains("invoice") -> "construction.quote.invoice"
        lower.contains("payment") || lower.contains("paid ") || lower.startsWith("record payment") -> "construction.payment.record"
        lower.contains("quote") && (lower.contains("create") || lower.contains("new") || lower.contains("make")) -> "construction.quote.create"
        lower.contains("lead") && (lower.contains("create") || lower.contains("new") || lower.contains("save")) -> "construction.lead.create"
        else -> null
    }

    private fun extractParams(
        intent: String,
        transcript: String,
        metadata: Map<String, Any?>,
    ): Map<String, Any?> = when (intent) {
        "construction.lead.create" -> extractLeadParams(transcript)
        "construction.quote.create" -> extractQuoteParams(transcript, metadata)
        "construction.payment.record" -> extractPaymentParams(transcript, metadata)
        "construction.quote.followup" -> extractQuoteRef(transcript, metadata)
        "construction.quote.invoice" -> extractQuoteRef(transcript, metadata)
        else -> emptyMap()
    }

    private fun extractLeadParams(transcript: String): Map<String, Any?> {
        val params = mutableMapOf<String, Any?>()
        extractClientName(transcript)?.let { params["client_name"] = it }
        extractJobType(transcript)?.let { params["job_type"] = it }
        extractLocation(transcript)?.let { params["location"] = it }
        extractEmail(transcript)?.let { params["email"] = it }
        parseMoney(transcript)?.let { params["estimated_budget"] = it.roundToInt() }
        params["urgency"] = when {
            transcript.contains("urgent", ignoreCase = true) ||
                transcript.contains("asap", ignoreCase = true) ||
                transcript.contains("emergency", ignoreCase = true) -> "high"
            transcript.contains("low priority", ignoreCase = true) -> "low"
            else -> "medium"
        }
        return params
    }

    private fun extractQuoteParams(
        transcript: String,
        metadata: Map<String, Any?>,
    ): Map<String, Any?> {
        val params = mutableMapOf<String, Any?>()
        extractSelectedId(metadata)?.let { params["lead_id"] = it }
        extractIdAfterKeyword(transcript, "lead")?.let { params["lead_id"] = it }
        extractMoneyAfterKeyword(transcript, "material")?.let { params["materials_cost"] = it }
        extractMoneyAfterKeyword(transcript, "labour")?.let { params["labor_cost"] = it }
        extractMoneyAfterKeyword(transcript, "labor")?.let { params["labor_cost"] = it }
        extractMarkup(transcript)?.let { params["markup_percent"] = it }
        if (!params.containsKey("markup_percent")) {
            params["markup_percent"] = 20
        }
        return params
    }

    private fun extractPaymentParams(
        transcript: String,
        metadata: Map<String, Any?>,
    ): Map<String, Any?> {
        val params = mutableMapOf<String, Any?>()
        extractSelectedId(metadata)?.let { params["quote_id"] = it }
        extractIdAfterKeyword(transcript, "quote")?.let { params["quote_id"] = it }
        parseMoney(transcript)?.let { params["amount"] = it }
        return params
    }

    private fun extractQuoteRef(
        transcript: String,
        metadata: Map<String, Any?>,
    ): Map<String, Any?> {
        val params = mutableMapOf<String, Any?>()
        extractSelectedId(metadata)?.let { params["quote_id"] = it }
        extractIdAfterKeyword(transcript, "quote")?.let { params["quote_id"] = it }
        return params
    }

    private fun parseCollectedValue(
        intent: String,
        key: String,
        transcript: String,
        metadata: Map<String, Any?>,
    ): Any? = when (key) {
        "estimated_budget", "materials_cost", "labor_cost", "amount" -> parseMoney(transcript)
        "markup_percent" -> extractMarkup(transcript)
        "lead_id", "quote_id" -> extractSelectedId(metadata)
            ?: extractIdAfterKeyword(transcript, if (key == "lead_id") "lead" else "quote")
            ?: transcript.filter(Char::isDigit).toIntOrNull()
        else -> transcript.trim()
    }

    private fun extractClientName(text: String): String? {
        val match = Regex("""(?:lead for|for)\s+([A-Za-z][A-Za-z\s'-]{1,40}?)(?:,|\sin\s|\sjob|\sbudget|$)""")
            .find(text)
        return match?.groupValues?.getOrNull(1)?.trim()?.takeIf { it.isNotBlank() }
    }

    private fun extractJobType(text: String): String? {
        val match = Regex("""([A-Za-z][A-Za-z\s/&-]{1,40}?)\s+job""").find(text)
        return match?.groupValues?.getOrNull(1)?.trim()?.takeIf { it.isNotBlank() }
    }

    private fun extractLocation(text: String): String? {
        val match = Regex("""(?:in|at)\s+([A-Za-z][A-Za-z\s'-]{1,40}?)(?:,|\sbudget|$)""").find(text)
        return match?.groupValues?.getOrNull(1)?.trim()?.takeIf { it.isNotBlank() }
    }

    private fun extractEmail(text: String): String? {
        val match = Regex("""[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}""", RegexOption.IGNORE_CASE)
            .find(text)
        return match?.value
    }

    private fun extractIdAfterKeyword(text: String, keyword: String): Int? {
        val match = Regex("""$keyword\s*#?\s*(\d+)""", RegexOption.IGNORE_CASE).find(text)
        return match?.groupValues?.getOrNull(1)?.toIntOrNull()
    }

    private fun extractSelectedId(metadata: Map<String, Any?>): Int? {
        val selected = metadata["selected_item_id"]
        return when (selected) {
            is Int -> selected
            is Long -> selected.toInt()
            is Double -> selected.roundToInt()
            is Float -> selected.roundToInt()
            is String -> selected.toIntOrNull()
            else -> null
        }
    }

    private fun extractMoneyAfterKeyword(text: String, keyword: String): Double? {
        val match = Regex(
            """$keyword[s]?(?:\s+cost)?(?:\s+(?:of|is))?\s+\$?([\d.,]+(?:\s*(?:k|grand|thousand))?)""",
            RegexOption.IGNORE_CASE,
        ).find(text)
        return match?.groupValues?.getOrNull(1)?.let { parseMoney(it) }
    }

    private fun extractMarkup(text: String): Int? {
        val match = Regex("""markup(?:\s+of)?\s+(\d{1,2})""", RegexOption.IGNORE_CASE).find(text)
        return match?.groupValues?.getOrNull(1)?.toIntOrNull()
    }

    private fun parseMoney(text: String): Double? {
        val match = Regex("""(\d+(?:\.\d+)?)\s*(k|grand|thousand)?""", RegexOption.IGNORE_CASE).find(text)
        val value = match?.groupValues?.getOrNull(1)?.toDoubleOrNull() ?: return null
        return when (match.groupValues.getOrNull(2)?.lowercase()) {
            "k", "grand", "thousand" -> value * 1000
            else -> value
        }
    }

    private fun currency(value: Double): String =
        "$" + String.format(Locale.US, "%,.0f", value)

    private fun confirmationPrompt(intent: String, params: Map<String, Any?>): String =
        when (intent) {
            "construction.lead.create" -> {
                val client = params["client_name"] ?: "this client"
                val jobType = params["job_type"] ?: "job"
                val location = params["location"] ?: "unknown location"
                val budget = (params["estimated_budget"] as? Number)?.toDouble()?.let(::currency)
                if (budget != null) {
                    "Create a lead for $client, $jobType in $location with budget $budget?"
                } else {
                    "Create a lead for $client, $jobType in $location?"
                }
            }

            "construction.quote.create" -> {
                val leadId = params["lead_id"] ?: "unknown"
                val materials = currency((params["materials_cost"] as? Number)?.toDouble() ?: 0.0)
                val labor = currency((params["labor_cost"] as? Number)?.toDouble() ?: 0.0)
                val markup = params["markup_percent"] ?: 20
                "Create a quote for lead #$leadId with materials $materials, labour $labor, markup $markup percent?"
            }

            "construction.payment.record" -> {
                val quoteId = params["quote_id"] ?: "unknown"
                val amount = currency((params["amount"] as? Number)?.toDouble() ?: 0.0)
                "Record payment of $amount for quote #$quoteId?"
            }

            "construction.quote.followup" -> {
                val quoteId = params["quote_id"] ?: "unknown"
                "Draft a follow-up for quote #$quoteId?"
            }

            "construction.quote.invoice" -> {
                val quoteId = params["quote_id"] ?: "unknown"
                "Prepare invoice work for quote #$quoteId?"
            }

            else -> "Confirm this offline action?"
        }

    private fun isPositive(text: String): Boolean {
        val lower = text.lowercase()
        return listOf("yes", "yep", "yeah", "confirm", "do it", "go ahead").any { lower.contains(it) }
    }

    private fun isNegative(text: String): Boolean {
        val lower = text.lowercase()
        return listOf("no", "nah", "cancel", "stop", "never mind").any { lower.contains(it) }
    }

    private fun parseModelIntent(raw: String): ModelIntentResult? {
        val jsonText = extractJsonObject(raw) ?: return null
        val root = JSONObject(jsonText)
        val intent = root.optString("intent")
        if (intent.isBlank()) return null

        val confidence = when (val value = root.opt("confidence")) {
            is Number -> value.toDouble()
            is String -> value.toDoubleOrNull() ?: 0.0
            else -> 0.0
        }
        val resultObject = root.optJSONObject("result") ?: JSONObject()
        return ModelIntentResult(
            intent = intent,
            confidence = confidence,
            result = jsonObjectToMap(resultObject),
        )
    }

    private fun extractJsonObject(raw: String): String? {
        val fenced = Regex(
            """```(?:json)?\s*(\{.*})\s*```""",
            setOf(RegexOption.DOT_MATCHES_ALL, RegexOption.IGNORE_CASE),
        ).find(raw)?.groupValues?.getOrNull(1)
        if (!fenced.isNullOrBlank()) {
            return fenced
        }
        val first = raw.indexOf('{')
        val last = raw.lastIndexOf('}')
        return if (first >= 0 && last > first) raw.substring(first, last + 1) else null
    }

    private fun jsonObjectToMap(jsonObject: JSONObject): Map<String, Any?> {
        val result = mutableMapOf<String, Any?>()
        val keys = jsonObject.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            result[key] = jsonValueToAny(jsonObject.opt(key))
        }
        return result
    }

    private fun jsonArrayToList(jsonArray: JSONArray): List<Any?> {
        val list = mutableListOf<Any?>()
        for (index in 0 until jsonArray.length()) {
            list += jsonValueToAny(jsonArray.opt(index))
        }
        return list
    }

    private fun jsonValueToAny(value: Any?): Any? = when (value) {
        null, JSONObject.NULL -> null
        is JSONObject -> jsonObjectToMap(value)
        is JSONArray -> jsonArrayToList(value)
        else -> value
    }

    fun close() {
        modelRuntime.close()
    }

    private class LocalModelInferenceEngine(
        private val context: Context,
    ) {
        private var engine: Engine? = null
        private var initializedModelPath: String? = null
        private val mutex = Mutex()

        suspend fun initializeModel(modelFile: File) {
            mutex.withLock {
                withContext(Dispatchers.IO) {
                    if (initializedModelPath == modelFile.absolutePath && engine != null) {
                        return@withContext
                    }
                    if (!modelFile.exists()) {
                        throw IllegalStateException("Model file not found in local app storage directory.")
                    }

                    engine?.close()
                    engine = createInitializedEngine(modelFile)
                    initializedModelPath = modelFile.absolutePath
                }
            }
        }

        fun isReady(): Boolean = engine != null

        fun isReadyFor(modelPath: String): Boolean =
            engine != null && initializedModelPath == modelPath

        @OptIn(ExperimentalApi::class)
        suspend fun extractTradieIntent(
            userInput: String,
            screenContext: String,
            metadata: Map<String, Any?>,
            onChunk: suspend (String) -> Unit = {},
        ): String = withContext(Dispatchers.IO) {
            val activeEngine = engine ?: return@withContext """{"error":"Model uninitialized"}"""
            val conversationConfig = ConversationConfig(
                systemInstruction = Contents.of(buildSystemPrompt(screenContext, metadata)),
            )

            activeEngine.createConversation(conversationConfig).use { conversation ->
                val message = conversation.sendMessage(userInput, emptyMap<String, Any>())
                val rendered = conversation
                    .renderMessageIntoString(message, emptyMap<String, Any>())
                    .trim()
                if (rendered.isNotBlank()) {
                    onChunk(rendered)
                }
                return@withContext rendered
            }
        }

        @OptIn(ExperimentalApi::class)
        suspend fun runPrompt(
            userInput: String,
            onChunk: suspend (String) -> Unit = {},
        ): String = withContext(Dispatchers.IO) {
            val activeEngine = engine ?: return@withContext "Model uninitialized."
            val conversationConfig = ConversationConfig(
                systemInstruction = Contents.of(
                    "You are BackPocket's on-device AI Edge assistant. Answer directly, keep private data on-device, and be concise unless the user asks for detail.",
                ),
            )

            activeEngine.createConversation(conversationConfig).use { conversation ->
                val message = conversation.sendMessage(userInput, emptyMap<String, Any>())
                val rendered = conversation
                    .renderMessageIntoString(message, emptyMap<String, Any>())
                    .trim()
                if (rendered.isNotBlank()) {
                    onChunk(rendered)
                }
                return@withContext rendered
            }
        }

        private fun createInitializedEngine(modelFile: File): Engine {
            val npuConfig = EngineConfig(
                modelPath = modelFile.absolutePath,
                backend = Backend.NPU(
                    nativeLibraryDir = context.applicationInfo.nativeLibraryDir,
                ),
                cacheDir = context.cacheDir.absolutePath,
            )

            return try {
                Engine(npuConfig).also { it.initialize() }
            } catch (_: Throwable) {
                val cpuConfig = EngineConfig(
                    modelPath = modelFile.absolutePath,
                    backend = Backend.CPU(),
                    cacheDir = context.cacheDir.absolutePath,
                )
                Engine(cpuConfig).also { it.initialize() }
            }
        }

        private fun buildSystemPrompt(
            screenContext: String,
            metadata: Map<String, Any?>,
        ): String {
            val selectedItemId = metadata["selected_item_id"] ?: ""
            val tabIndex = metadata["tab_index"] ?: ""
            return """
                You are the BackPocket OS local intent extractor for Australian tradies.
                Screen context: $screenContext
                Selected item id: $selectedItemId
                Tab index: $tabIndex

                Supported intents:
                - construction.lead.create
                - construction.quote.create
                - construction.payment.record
                - construction.quote.followup
                - construction.quote.invoice
                - dashboard.summary
                - navigate.screen

                Return JSON only.
                Schema:
                {
                  "intent": String,
                  "confidence": Float,
                  "result": {
                    "client_name": String?,
                    "job_type": String?,
                    "location": String?,
                    "estimated_budget": Int?,
                    "lead_id": Int?,
                    "quote_id": Int?,
                    "materials_cost": Double?,
                    "labor_cost": Double?,
                    "markup_percent": Int?,
                    "amount": Double?,
                    "screen": String?
                  }
                }

                Use null for unknown fields. Do not add markdown.
            """.trimIndent()
        }

        fun close() {
            engine?.close()
            engine = null
            initializedModelPath = null
        }
    }
}
