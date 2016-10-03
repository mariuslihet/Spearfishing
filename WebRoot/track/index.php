<?php
ignore_user_abort(); //Continue processing if the browser drops the connection
$logfile = '/someplace/logfile.txt';
$dbpath = '/someplace/spearphish.db';

$hash = $_REQUEST['v'];
if (empty($hash))
    $hash = 'unknown';
$to = $_REQUEST['to'];
foreach ($_GET as $key => $value)
{
    if (!(stristr($key, 'v')) && !(stristr($key, 'm')) && !(stristr($key, 'to')))
        $to .= "&" . $key . "=" . $value;
}
if (empty($to))
    $to = 'unknown';
//Push the response to the browser as soon as possible
header("Location: " . $to);
header("Connection: close");
header("Content-Length: 0");
flush();

//Ignore clicks from unmerged templates
if ('__victim__' == $hash) {
    exit;
}

//$_REQUEST['m'] should contain the mailing_id
$mailing_id = $_REQUEST['m'];
if (empty($mailing_id))
    $mailing_id = '0';
$ip = $_SERVER['REMOTE_ADDR'];
$time = gmdate('Y-m-d H:i:s');
$db = new PDO('sqlite:' . $dbpath);

// make sure to log the raw values, regardless whether they can be resolved
$mail = $hash;
$pretext = $mailing_id;
try
{
    // Look up email address from hash
    $query = $db->prepare('SELECT mail FROM user WHERE md5sum = ?');
    $query->execute([$hash]);
    $user = $query->fetch(PDO::FETCH_NUM);
    if (false !== $user) {
        $mail = $user[0];
 //       $query = $db->prepare('UPDATE user SET enabled = 0 WHERE usergroup != \'ros_group\' and md5sum = ?');
 //       $query->execute([$hash]);
    }
    // Look up mailing pretext name from mailing ID
    $query = $db->prepare('SELECT pretext FROM sent WHERE mailing_id = ?');
    $query->execute([$mailing_id]);
    $pretextinfo = $query->fetch(PDO::FETCH_NUM);
    if (false !== $pretextinfo) {
        $pretext = $pretextinfo[0];
    }
    $db = NULL;
}
catch(PDOException $e)
{
    print 'Exception : '.$e->getMessage();
}

// print('received from ' . $hash . ' (' . $ip. ') at ' . $time . ', mailing ID ' . $m. ', redirecting to ' . $to);
//Log the event
$fp = fopen($logfile, 'a');
while (1) {
    if (flock($fp, LOCK_EX)) {
        fputcsv($fp, [$time, $mail, $ip, $mailing_id, $pretext, $to], ',', '"');
        flock($fp, LOCK_UN);
        break;
    }
}
fclose($fp);


$url = 'http://your-hubot-server/hubot/clicktrack/' . $mail;
$data = array('key1' => 'value1', 'key2' => 'value2');

// use key 'http' even if you send the request to https://...
$options = array(
    'http' => array(
        'header'  => "Content-type: application/x-www-form-urlencoded\r\n",
        'method'  => 'POST',
        'content' => http_build_query($data),
    ),
);
$ch = curl_init();
curl_setopt($ch,CURLOPT_URL,$url);
curl_setopt($ch,CURLOPT_POST,count($data));
curl_setopt($ch,CURLOPT_POSTFIELDS,"{}");
$result = curl_exec($ch);


