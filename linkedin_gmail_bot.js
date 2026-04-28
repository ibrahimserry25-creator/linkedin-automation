// ==========================================
// 🚀 نظام الرد التلقائي عبر الجيميل للينكدإن
// ==========================================

// 1️⃣ حط مفاتيحك هنا:
var GEMINI_API_KEY = "AIzaSyC0brZIBZwd7QkKhv3L0J7gFh80cioKndY";
var LINKEDIN_ACCESS_TOKEN = "AQUQE7QfgNR13afHokf-VevhtYH4mKkEnOimiT0OlVYp359pDk4qja1Euolzte1klbK_TqrL7NVVhM8bms11Bkma4Sj68nYcs1qM8xqjwUXGg92B3ix8CjxhEKVw_MugluitE5Hu5dsUdrElgnHsMswd1rXRvgngd-Pz2R1wz2W-D-HKk0ZK4tD7N9uREtE7NYSaZ3n9LLYtpAPhZL_0Nvtv2R-9owE6LDVczBG5INat1b2SLDU9nJvJeRb5TmL_6pB2RicVPzRAYtst6G9e5gw382OZFcZ7LusLl3xbbasCcmzA07IdQD1ZV163EMvEEQ1hv4FF_sITFXQ5k5ScvS_AXW-p5A";
var TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here";
var TELEGRAM_CHAT_ID = "your_telegram_chat_id_here";

// الدالة الرئيسية اللي هتشتغل كل 5 دقايق
function checkLinkedInComments() {
  // البحث عن إيميلات التعليقات الجديدة اللي لسة متقرتش
  var threads = GmailApp.search('from:messages-noreply@linkedin.com "commented on your" is:unread', 0, 5);
  
  if (threads.length === 0) {
    return; // مفيش تعليقات جديدة
  }
  
  // بنجيب URN الخاص بيك عشان نرد باسمك
  var myPersonUrn = getMyLinkedInUrn();
  if (!myPersonUrn) {
    sendTelegram("❌ فشل الحصول على معرّف لينكدإن الخاص بك. تأكد من صحة LINKEDIN_ACCESS_TOKEN");
    return;
  }
  
  for (var i = 0; i < threads.length; i++) {
    var message = threads[i].getMessages()[0];
    var htmlBody = message.getBody();
    var plainBody = message.getPlainBody();
    
    // استخراج معرّف المنشور (URN) من الإيميل عشان نرد عليه
    var urnMatch = htmlBody.match(/(urn(?:%3A|:)li(?:%3A|:)(?:share|ugcPost|activity)(?:%3A|:)\d+)/i);
    if (!urnMatch) {
      message.markRead(); // لو مفيش URN نعلمها مقروءة ونتخطاها
      continue;
    }
    
    var targetUrn = decodeURIComponent(urnMatch[1]);
    
    // استخراج التعليق واسم الشخص باستخدام جيميني للذكاء
    var commentData = extractCommentWithGemini(plainBody);
    if (!commentData || !commentData.comment || commentData.comment.length < 2) {
      message.markRead();
      continue;
    }
    
    // توليد الرد الذكي
    var replyText = generateReplyWithGemini(commentData.author, commentData.comment);
    if (!replyText) {
      continue;
    }
    
    // نشر الرد على لينكدإن
    var success = postCommentToLinkedIn(targetUrn, myPersonUrn, replyText);
    
    if (success) {
      sendTelegram("💬 <b>رد تلقائي جديد (من الإيميل)</b>\n\n👤 <b>الشخص:</b> " + commentData.author + "\n📝 <b>تعليقه:</b> " + commentData.comment + "\n\n🤖 <b>الرد:</b> " + replyText);
    } else {
      sendTelegram("❌ فشل الرد التلقائي على تعليق من الإيميل.");
    }
    
    message.markRead(); // نعلمها مقروءة عشان ميردش عليها تاني
  }
}

function getMyLinkedInUrn() {
  try {
    var response = UrlFetchApp.fetch("https://api.linkedin.com/v2/userinfo", {
      headers: { "Authorization": "Bearer " + LINKEDIN_ACCESS_TOKEN },
      muteHttpExceptions: true
    });
    if (response.getResponseCode() == 200) {
      var data = JSON.parse(response.getContentText());
      return "urn:li:person:" + data.sub;
    }
  } catch (e) {
    Logger.log("Error getting userinfo: " + e);
  }
  return null;
}

function postCommentToLinkedIn(targetUrn, actorUrn, replyText) {
  var url = "https://api.linkedin.com/v2/socialActions/" + encodeURIComponent(targetUrn) + "/comments";
  var payload = {
    "actor": actorUrn,
    "message": { "text": replyText }
  };
  
  var options = {
    "method": "post",
    "contentType": "application/json",
    "headers": {
      "Authorization": "Bearer " + LINKEDIN_ACCESS_TOKEN,
      "X-Restli-Protocol-Version": "2.0.0"
    },
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };
  
  try {
    var response = UrlFetchApp.fetch(url, options);
    if (response.getResponseCode() == 201 || response.getResponseCode() == 200) {
      return true;
    } else {
      Logger.log("Failed to post: " + response.getContentText());
      return false;
    }
  } catch (e) {
    Logger.log("Exception posting: " + e);
    return false;
  }
}

function extractCommentWithGemini(emailBody) {
  var prompt = "هذا نص إيميل من لينكدإن يخبرني أن شخصاً علق على منشوري. استخرج اسم الشخص ونص تعليقه بدقة. أرجع الناتج بصيغة JSON فقط كالتالي: {\"author\": \"الاسم\", \"comment\": \"التعليق\"}. لا تكتب أي شيء آخر.\n\nالنص:\n" + emailBody.substring(0, 1500);
  
  var url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY;
  var payload = {
    "contents": [{"parts": [{"text": prompt}]}]
  };
  
  try {
    var response = UrlFetchApp.fetch(url, {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(payload),
      "muteHttpExceptions": true
    });
    
    var data = JSON.parse(response.getContentText());
    var text = data.candidates[0].content.parts[0].text;
    text = text.replace(/```json/g, "").replace(/```/g, "").trim();
    return JSON.parse(text);
  } catch (e) {
    Logger.log("Error extracting comment: " + e);
    return null;
  }
}

function generateReplyWithGemini(author, commentText) {
  var prompt = "أنت تدير حسابي الشخصي على لينكدإن بالنيابة عني. قام شخص يدعى '" + author + "' بكتابة هذا التعليق على منشوري:\n\"" + commentText + "\"\n\nاكتب رداً مختصراً جداً (جملة واحدة أو جملتين كحد أقصى) باللغة العربية، يكون احترافياً ولطيفاً وطبيعياً جداً وكأنني أنا من أرد. لا تضع أي تنسيقات مثل البولد أو الماركدون، فقط نص الرد.";
  
  var url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY;
  var payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.7}
  };
  
  try {
    var response = UrlFetchApp.fetch(url, {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(payload),
      "muteHttpExceptions": true
    });
    
    var data = JSON.parse(response.getContentText());
    return data.candidates[0].content.parts[0].text.trim();
  } catch (e) {
    Logger.log("Error generating reply: " + e);
    return null;
  }
}

function sendTelegram(message) {
  var url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage";
  UrlFetchApp.fetch(url, {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify({
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "HTML"
    }),
    "muteHttpExceptions": true
  });
}
