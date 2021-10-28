��    '      T              �     �     �  C   �  ,   �       d   ,  1   �  *   �  S   �  I   B  �   �  �   Z     �  M   �     >     N     U  
   ^  F   i     �     �     �  ;   �  @   -  p   n     �     �  $        '     E     M  �   g  
   	     	  _   6	  C   �	  �   �	  �   [
  �  �
     e     r  W   �  -   �       x     <   �  4   �  d   
  S   o     �  �   �     �  Q   �          #     *  
   7  W   B     �     �     �  =   �  K     u   i     �     �  /   	  $   9     ^     f  �   �     A     M  }   m  K   �  �   7  �   �   About OctoPi Advanced options Allows to check for the Pi's throttling status and environment info Command for under voltage/overheat detection Current issues: Defaults to <code>/usr/bin/vcgencmd get_throttled</code>. You usually shouldn't have to change this. Disable warning about undervoltage on print start Disable warning about unsupported hardware Enable under voltage and overheat detection via <code>vcgencmd get_throttled</code> Frequency capping due to overheating. Improve cooling of the CPU and GPU. If you check this, you will no longer get warned if you run OctoPrint on Raspberry Pi models that are not officially supported due to bad performance that can lead to failed prints. Do so at your own risk. If you check this, you will no longer get warned when starting prints during observed undervoltage issues. Do so at your own risk. Issues since boot: Make sure your power supply and cabling are providing enough power to the Pi. No, don't print OctoPi Overheat Pi Support Please restart OctoPrint after changing any of this plugin's settings. See also the FAQ See also the FAQ... Start the print job anyway? The following issues are being observed <em>right now</em>: The following issues have been observed since the Pi was booted: This will regularly check with the Pi if something is amiss either with power regulation or CPU/GPU temperature. Undervoltage Undervoltage detected Undervoltage detected, print anyway? Unsupported hardware detected Warning What do the symbols mean? Without this plugin OctoPrint will no longer be able to provide additional information about your Pi, which will make it more tricky to help you if you need support. Yes, print Yes, print & don't warn again You can disable this message via Settings > Pi Support > Ignore warning on unsupported hardware You can read more <a href="%(url)s" target="_blank">in the FAQ</a>. Your Pi is reporting undervoltage. It is not recommended to start a print job until an adequate power supply has been installed. Your Raspberry Pi is reporting insufficient power. Switch to an adequate power supply or risk bad performance and failed prints. Project-Id-Version: OctoPrint-PiSupport 2021.10.28
Report-Msgid-Bugs-To: i18n@octoprint.org
POT-Creation-Date: 2021-10-28 09:18+0200
PO-Revision-Date: 2021-06-14 18:16+0200
Last-Translator: 
Language: de
Language-Team: de <LL@li.org>
Plural-Forms: nplurals=2; plural=(n != 1)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.8.0
 Über OctoPi Erweiterte Optionen Erlaubt die Abfrage des Throttlestatus und der Umgebungsinformationen des Raspberry Pis Befehl für Spannungs-/Überhitzungserkennung Aktuelle Probleme: Standardeinstellung ist <code>/usr/bin/vcgencmd get_throttled</code>. Du solltest das gewöhnlich nicht ändern müssen. Ignoriere Warnung über zu niedrige Spannung beim Druckstart Ignoriere Warnung über nicht unterstützte Hardware Erkennung zu niedriger Spannung und Überhitzung via <code>vcgencmd get_throttled</code> einschalten Heruntertaktung aufgrund von Überhitzung. Verbessere die Kühlung von CPU und GPU. Falls du das aktivierst, wird dich OctoPrint nicht mehr davor warnen, wenn du es auf Raspberry Pi Modellen laufen lässt, die aufgrund bekannter Probleme mit Performance und fehlgeschlagenen Druckaufträgen nicht offiziell unterstützt werden. Du tust dies auf deine eigene Verantwortung. Wenn du das aktivierst, wird OctoPrint dich nicht mehr warnen, wenn du einen Druckjob startest während dein Pi zu niedrige Spannung meldet. Du tust dies auf deine eigene Verantwortung. Probleme seit dem Bootvorgang: Stelle sicher, dass dein Netzteil und die Verkabelung dem Pi genug Strom liefern. Nein, nicht drucken OctoPi Überhitzung Pi Support Bitte starte OctoPrint neu, nachdem du die Einstellungen dieses Plugins geändert hast. Siehe also die FAQ Siehe also die FAQ... Den Druck trotzdem starten? Die folgenden Probleme werden <em>gerade jetzt</em> gemeldet: Die folgenden Probleme wurde seit dem letzten Bootvorgang des Pis gemeldet: Es wird regelmäßig geprüft, ob etwas mit der Spannungsversorgung oder der CPU/GPU Temperatur des Pis nicht stimmt. Zu niedrige Spannung Zu niedrige Spannung Zu niedrige Spannung erkannt, trotzdem drucken? Nicht unterstützte Hardware erkannt Warnung Was bedeuten die Symbole? Ohne dieses Plugin kann OctoPrint nicht mehr zusätzliche Informationen über deinen Pi Instanz zur Verfügung stellen, was es ggf. schwieriger macht, dir zu helfen, falls du Support brauchst. Ja, drucken Ja, drucken & nicht mehr warnen Du kannst diese Nachricht deaktiveren über Einstellungen > Pi Support > Ignoriere Warnung über nicht unterstützte Hardware Du kannst mehr dazu <a href="%(url)s" target="_blank">in der FAQ</a> lesen. Dein Pi meldet eine zu niedrige Spannung. Es ist nicht empfohlen, einen Druckauftrag zu starten, bis ein ausreichendes Netzteil installiert ist. Dein Raspberry Pi meldet eine zu niedrige Spannung. Wechsle auf ein ausreichendes Netzteil, oder riskiere schlechte Performance und fehlgeschlagene Druckaufträge. 