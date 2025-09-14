package com.example.tessen

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.example.tessen.ui.theme.TESSENTheme

class MainActivity : ComponentActivity() {
    private lateinit var bluetoothAdapter: BluetoothAdapter
    private var isBluetoothEnabled by mutableStateOf(false)
    private var isScanning by mutableStateOf(false)

    // 권한 요청 런처
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (allGranted) {
            startBluetoothScan()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Bluetooth 어댑터 초기화
        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothAdapter = bluetoothManager.adapter

        setContent {
            TESSENTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    TessenApp(
                        modifier = Modifier.padding(innerPadding),
                        isBluetoothEnabled = isBluetoothEnabled,
                        isScanning = isScanning,
                        onBluetoothToggle = { enableBluetooth() },
                        onScanToggle = { toggleScan() }
                    )
                }
            }
        }
    }

    private fun enableBluetooth() {
        if (!bluetoothAdapter.isEnabled) {
            // Bluetooth 활성화 요청
            val enableBtIntent = android.content.Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
            startActivity(enableBtIntent)
        }
        isBluetoothEnabled = bluetoothAdapter.isEnabled
    }

    private fun toggleScan() {
        if (isScanning) {
            stopBluetoothScan()
        } else {
            checkPermissionsAndScan()
        }
    }

    private fun checkPermissionsAndScan() {
        val permissions = arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.ACCESS_FINE_LOCATION
        )

        val allGranted = permissions.all { permission ->
            ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED
        }

        if (allGranted) {
            startBluetoothScan()
        } else {
            requestPermissionLauncher.launch(permissions)
        }
    }

    private fun startBluetoothScan() {
        isScanning = true
        // TODO: 실제 Bluetooth LE 스캔 구현
    }

    private fun stopBluetoothScan() {
        isScanning = false
        // TODO: Bluetooth LE 스캔 중지
    }
}

@Composable
fun TessenApp(
    modifier: Modifier = Modifier,
    isBluetoothEnabled: Boolean,
    isScanning: Boolean,
    onBluetoothToggle: () -> Unit,
    onScanToggle: () -> Unit
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 제목
        Text(
            text = "TESSEN Tennis Sensor",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(32.dp))

        // Bluetooth 상태
        Card(
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Bluetooth 상태",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Medium
                )
                Text(
                    text = if (isBluetoothEnabled) "활성화됨" else "비활성화됨",
                    color = if (isBluetoothEnabled) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
                )

                Button(
                    onClick = onBluetoothToggle,
                    modifier = Modifier.padding(top = 8.dp)
                ) {
                    Text(if (isBluetoothEnabled) "Bluetooth 끄기" else "Bluetooth 켜기")
                }
            }
        }

        // 스캔 버튼
        Button(
            onClick = onScanToggle,
            enabled = isBluetoothEnabled,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(if (isScanning) "스캔 중지" else "TESSEN 센서 스캔")
        }

        // 센서 데이터 영역
        Card(
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(
                    text = "센서 데이터",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Medium
                )
                Text(
                    text = if (isScanning) "TESSEN 센서를 찾는 중..." else "센서를 연결하세요",
                    modifier = Modifier.padding(top = 8.dp)
                )
            }
        }
    }
}