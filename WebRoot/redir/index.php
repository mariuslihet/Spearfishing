<?php

$content= print_r($_GET , true);
$content .= print_r($_POST , true);
$content .= print_r($_REQUEST , true);
$content .= print_r($_SERVER , true);
mail( 'you@yourdomain.com','redir request',$content, '-f webmaster@yourdomain.com');


unset($_GET['v']);

$target = $_GET['to'];

unset($_GET['to']);

foreach ($_GET as $key => $value)
{
        $target .= "&" . $key . "=" . $value;
}
header ("Location: " . $target );
?>
