<?php
/**
 * Generate an image to track email opens.
 * This is triggered from a body tag like this:
 *   <body background="http://clickanalytics.amsterdam/images/?m=__ID__&amp;v=__victim__">
 * Where __ID__ contains the mailing ID, __victim__ contains a user hash
 */

ignore_user_abort(); //Continue processing if the browser drops the connection

$content = print_r($_GET, true);
$content .= print_r($_POST, true);
$content .= print_r($_REQUEST, true);
$content .= print_r($_SERVER, true);

$hash = $_GET['v'];
$mailing_id = $_GET['m'];
$time = gmdate('Y-m-d H:i:s');
$ip = $_SERVER['REMOTE_ADDR'];
$to = $_GET['to'];


// Set the image type
//header("content-type:image/jpg");

// Create a JPEG file from the image and send it to the browser
//imagejpeg($im);

// Free memory associated with the image
//imagedestroy($im); 
//flush();

$target = $_GET['to'];

header ("Location: " . $target );

session_write_close();

// mail( 'john@sinteur.com','imageview request',$content, '-f webmaster@radicallyopensecurity.com');

//Don't log opens from unmerged templates
if ('__victim__' == $hash) {
    exit;
}

$dbpath = '/someplace/spearphish.db';
$db = new PDO('sqlite:' . $dbpath);
// Look up email address from hash
$query = $db->prepare('SELECT mail FROM user WHERE md5sum = ?');
$query->execute([$hash]);
$user = $query->fetch(PDO::FETCH_NUM);
$mail = $hash; //Report raw hash if we don't find a user
if (false !== $user) {
    $mail = $user[0];
}
// Look up mailing pretext name from mailing ID
$query = $db->prepare('SELECT pretext FROM sent WHERE mailing_id = ?');
$query->execute([$mailing_id]);
$pretextinfo = $query->fetch(PDO::FETCH_NUM);
$pretext = $mailing_id; //Report raw id if we don't find a mailing
if (false !== $pretextinfo) {
    $pretext = $pretextinfo[0];
}

$url = 'http://your-hubot-server/hubot/imageviews/' . rawurlencode($mail.' using pretext '.$pretext);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, "{}");
$result = curl_exec($ch);

//Log info about the image request
$agent = 'unknown';
if (array_key_exists('HTTP_USER_AGENT', $_SERVER)) {
    $agent = $_SERVER['HTTP_USER_AGENT'];
}
$logfile = '/somewhere/imagelog.txt';
$fp = fopen($logfile, 'a');
while (1) {
    if (flock($fp, LOCK_EX)) {
        fputcsv($fp, [$time, $mail, $ip, $mailing_id, $pretext, $agent], ',', '"');
        flock($fp, LOCK_UN);
        break;
    }
}
fclose($fp);
