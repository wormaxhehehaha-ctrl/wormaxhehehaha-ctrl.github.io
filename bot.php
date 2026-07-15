<?php
$BOT_TOKEN = '8801860264:AAGeuZSJxC34D85o8Iy1PeKu4ueJmC1NLd8';
$ADMIN_ID = '1817914190';
$API_URL = 'https://api.telegram.org/bot' . $BOT_TOKEN;

function sendMessage($chat_id, $text, $reply_markup = null) {
    global $API_URL;
    $data = ['chat_id' => $chat_id, 'text' => $text, 'parse_mode' => 'HTML'];
    if ($reply_markup) $data['reply_markup'] = json_encode($reply_markup);
    
    $ch = curl_init($API_URL . '/sendMessage');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
}

function sendDocument($chat_id, $file_path) {
    global $API_URL;
    $data = ['chat_id' => $chat_id, 'document' => new CURLFile($file_path)];
    
    $ch = curl_init($API_URL . '/sendDocument');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
}

function answerCallback($callback_id, $text) {
    global $API_URL;
    $data = ['callback_query_id' => $callback_id, 'text' => $text];
    
    $ch = curl_init($API_URL . '/answerCallbackQuery');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
}

function getKey($type, $user_id) {
    $botKeys = json_decode(file_get_contents('bot_keys.json'), true) ?: ['trial'=>[],'week'=>[],'month'=>[]];
    $trialUsers = json_decode(file_get_contents('trial_users.json'), true) ?: [];
    
    if ($type === 'trial') {
        if (in_array($user_id, $trialUsers)) return ['error' => 'Trial already used!'];
    }
    
    if (empty($botKeys[$type])) return ['error' => 'No keys available'];
    
    $keyData = array_shift($botKeys[$type]);
    $key = is_array($keyData) ? ($keyData['key'] ?? '') : $keyData;
    
    $botKeys[$type] = array_values($botKeys[$type]);
    file_put_contents('bot_keys.json', json_encode($botKeys));
    
    if ($type === 'trial') {
        $trialUsers[] = $user_id;
        file_put_contents('trial_users.json', json_encode($trialUsers));
    }
    
    return ['success' => true, 'key' => $key];
}

// Получаем обновления
$update = json_decode(file_get_contents('php://input'), true);

if (!$update) {
    // Запускаем long polling
    $offset = 0;
    while (true) {
        $ch = curl_init($API_URL . '/getUpdates?offset=' . $offset . '&timeout=30');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $response = curl_exec($ch);
        curl_close($ch);
        
        $updates = json_decode($response, true);
        
        if (isset($updates['result'])) {
            foreach ($updates['result'] as $update) {
                $offset = $update['update_id'] + 1;
                processUpdate($update);
            }
        }
    }
} else {
    processUpdate($update);
}

function processUpdate($update) {
    global $ADMIN_ID;
    
    // Message
    if (isset($update['message'])) {
        $msg = $update['message'];
        $chat_id = $msg['chat']['id'];
        $text = $msg['text'] ?? '';
        $user_id = $msg['from']['id'];
        
        if ($text == '/start' || $text == 'Start') {
            $kb = [
                'keyboard' => [['🔬 FREE Trial', '💳 Buy Plan'], ['👤 Profile', '💬 Support']],
                'resize_keyboard' => true
            ];
            sendMessage($chat_id, "⚡ CODM ELITE SHOP\n\n/buy - Purchase\n/profile - Status", $kb);
        }
        elseif ($text == '/buy' || strpos($text, 'Buy') !== false) {
            $kb = [
                'inline_keyboard' => [
                    [['text' => '🔬 FREE Trial', 'callback_data' => 'trial']],
                    [['text' => '📅 Week - 15$', 'callback_data' => 'week']],
                    [['text' => '🗓️ Month - 30$', 'callback_data' => 'month']]
                ]
            ];
            sendMessage($chat_id, "💳 Choose plan:", $kb);
        }
        elseif ($text == '/profile' || strpos($text, 'Profile') !== false) {
            $trialUsers = json_decode(file_get_contents('trial_users.json'), true) ?: [];
            $hasTrial = in_array((string)$user_id, $trialUsers);
            sendMessage($chat_id, "👤 Profile\n\nID: {$user_id}\nTrial: " . ($hasTrial ? 'USED' : 'AVAILABLE'));
        }
        elseif ($text == '/support' || strpos($text, 'Support') !== false) {
            sendMessage($chat_id, "💬 @idkidk1010");
        }
        elseif (strpos($text, 'Trial') !== false) {
            $result = getKey('trial', (string)$user_id);
            if (isset($result['key'])) {
                sendMessage($chat_id, "✅ Key: {$result['key']}\n⏰ 6 hours\n📱 1 device\n\n📥 APK: http://keycodm.atwebpages.com/app.apk");
            } else {
                sendMessage($chat_id, "❌ {$result['error']}");
            }
        }
        elseif ($text == '/test' && (string)$user_id === $ADMIN_ID) {
            $kb = [
                'inline_keyboard' => [
                    [['text' => 'Test Trial', 'callback_data' => 'adm_trial']],
                    [['text' => 'Test Week', 'callback_data' => 'adm_week']],
                    [['text' => 'Test Month', 'callback_data' => 'adm_month']]
                ]
            ];
            sendMessage($chat_id, "🧪 ADMIN TEST", $kb);
        }
    }
    
    // Callback
    if (isset($update['callback_query'])) {
        $cb = $update['callback_query'];
        $chat_id = $cb['message']['chat']['id'];
        $msg_id = $cb['message']['message_id'];
        $data = $cb['data'];
        $user_id = $cb['from']['id'];
        
        if ($data == 'trial') {
            $result = getKey('trial', (string)$user_id);
            if (isset($result['key'])) {
                sendMessage($chat_id, "✅ Key: {$result['key']}\n⏰ 6 hours\n📱 1 device\n\n📥 APK: http://keycodm.atwebpages.com/app.apk");
                answerCallback($cb['id'], 'Sent!');
            } else {
                answerCallback($cb['id'], $result['error']);
            }
        }
        elseif (in_array($data, ['week', 'month'])) {
            $price = $data == 'month' ? '30' : '15';
            $settings = json_decode(file_get_contents('bot_settings.json'), true);
            $kb = [
                'inline_keyboard' => [
                    [['text' => 'TON', 'callback_data' => "net_{$data}_TON"], ['text' => 'TRC20', 'callback_data' => "net_{$data}_TRC20"]],
                    [['text' => 'BEP20', 'callback_data' => "net_{$data}_BEP20"], ['text' => 'ERC20', 'callback_data' => "net_{$data}_ERC20"]]
                ]
            ];
            
            $ch = curl_init($GLOBALS['API_URL'] . '/editMessageText');
            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, [
                'chat_id' => $chat_id,
                'message_id' => $msg_id,
                'text' => strtoupper($data) . " - {$price}$\n\nChoose network:",
                'reply_markup' => json_encode($kb)
            ]);
            curl_exec($ch);
            curl_close($ch);
            
            answerCallback($cb['id'], '');
        }
        elseif (strpos($data, 'net_') === 0) {
            $parts = explode('_', $data);
            $plan = $parts[1];
            $net = $parts[2];
            $settings = json_decode(file_get_contents('bot_settings.json'), true);
            $wallet = $settings['usdt_wallets'][$net] ?? 'Not set';
            $price = $plan == 'month' ? '30' : '15';
            
            $kb = [
                'inline_keyboard' => [
                    [['text' => '✅ GET KEY', 'callback_data' => "get_{$plan}"]]
                ]
            ];
            
            $ch = curl_init($GLOBALS['API_URL'] . '/editMessageText');
            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, [
                'chat_id' => $chat_id,
                'message_id' => $msg_id,
                'text' => "Send {$price}$ USDT\n\n{$net}: {$wallet}\n\nClick GET KEY after paying",
                'reply_markup' => json_encode($kb)
            ]);
            curl_exec($ch);
            curl_close($ch);
            
            answerCallback($cb['id'], '');
        }
        elseif (strpos($data, 'get_') === 0) {
            $plan = str_replace('get_', '', $data);
            $result = getKey($plan, (string)$user_id);
            
            if (isset($result['key'])) {
                $dur = $plan == 'month' ? '30 days' : '7 days';
                $dev = $plan == 'month' ? '5 devices' : '1 device';
                sendMessage($chat_id, "✅ Key: {$result['key']}\n📅 {$dur}\n📱 {$dev}\n\n📥 APK: http://keycodm.atwebpages.com/app.apk");
                answerCallback($cb['id'], 'Sent!');
            } else {
                answerCallback($cb['id'], $result['error']);
            }
        }
        elseif (strpos($data, 'adm_') === 0) {
            if ((string)$user_id !== $ADMIN_ID) return;
            $plan = str_replace('adm_', '', $data);
            $result = getKey($plan, 'admin_test');
            if (isset($result['key'])) {
                sendMessage($chat_id, "✅ TEST: {$result['key']}");
                answerCallback($cb['id'], 'Sent!');
            }
        }
    }
}
?>