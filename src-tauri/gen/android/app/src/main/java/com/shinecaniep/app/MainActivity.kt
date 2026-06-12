package com.shinecaniep.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebView
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : TauriActivity() {
    companion object {
        private const val TAG = "MainActivity"
    }

    /** Pending WebView permission request, waiting for Android runtime permission result */
    private var pendingPermissionRequest: PermissionRequest? = null

    /** Activity result launcher for requesting Android runtime permissions */
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        // After Android permissions are resolved, grant the pending WebView request
        pendingPermissionRequest?.let { request ->
            val allGranted = request.resources.all { resource ->
                when (resource) {
                    PermissionRequest.RESOURCE_VIDEO_CAPTURE ->
                        results[Manifest.permission.CAMERA] == true
                    PermissionRequest.RESOURCE_AUDIO_CAPTURE ->
                        results[Manifest.permission.RECORD_AUDIO] == true
                    else -> true // Unknown resources are granted by default
                }
            }
            if (allGranted) {
                request.grant(request.resources)
            } else {
                request.deny()
            }
            pendingPermissionRequest = null
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        // Request essential Android runtime permissions on first launch
        requestEssentialPermissions()
    }

    override fun onWebViewCreate(webView: WebView) {
        super.onWebViewCreate(webView)

        // Set a custom WebChromeClient that handles WebView permission requests
        // (camera, microphone, etc.) and bridges them to Android runtime permissions
        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                // Determine which Android permissions are needed for the WebView request
                val neededAndroidPermissions = mutableListOf<String>()

                for (resource in request.resources) {
                    when (resource) {
                        PermissionRequest.RESOURCE_VIDEO_CAPTURE -> {
                            if (!hasPermission(Manifest.permission.CAMERA)) {
                                neededAndroidPermissions.add(Manifest.permission.CAMERA)
                            }
                        }
                        PermissionRequest.RESOURCE_AUDIO_CAPTURE -> {
                            if (!hasPermission(Manifest.permission.RECORD_AUDIO)) {
                                neededAndroidPermissions.add(Manifest.permission.RECORD_AUDIO)
                            }
                        }
                    }
                }

                if (neededAndroidPermissions.isEmpty()) {
                    // All Android permissions already granted, approve the WebView request
                    request.grant(request.resources)
                } else {
                    // Save the WebView request and ask Android for runtime permissions
                    pendingPermissionRequest = request
                    requestPermissionLauncher.launch(neededAndroidPermissions.toTypedArray())
                }
            }
        }
    }

    /**
     * Request essential Android runtime permissions on app startup.
     * This covers camera, audio, Bluetooth, and location.
     */
    private fun requestEssentialPermissions() {
        val permissions = buildList {
            add(Manifest.permission.CAMERA)
            add(Manifest.permission.RECORD_AUDIO)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                add(Manifest.permission.BLUETOOTH_CONNECT)
                add(Manifest.permission.BLUETOOTH_SCAN)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                add(Manifest.permission.ACCESS_FINE_LOCATION)
            } else {
                add(Manifest.permission.ACCESS_COARSE_LOCATION)
            }
        }

        val ungranted = permissions.filter { !hasPermission(it) }
        if (ungranted.isNotEmpty()) {
            requestPermissionLauncher.launch(ungranted.toTypedArray())
        }
    }

    private fun hasPermission(permission: String): Boolean {
        return ContextCompat.checkSelfPermission(
            this, permission
        ) == PackageManager.PERMISSION_GRANTED
    }
}
