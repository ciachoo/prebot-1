#include <pluginapi.h>
#include <time.h>
#include "../commands/interface.h"
#include <toolbox/tb_string.h>

#define PLUG_NAME "pivo"

typedef struct {
	int minut_na_pivo;
	int max_piv;
	time_t posledni_pivo;

	EVENT_HANDLER *onpivo;
} pivo_data;

void pivo_command(EVENT *event) {
	pivo_data *pivo = (pivo_data *)event->handlerData;
	Commands_Event *cmd = (Commands_Event *)event->customData;
	IRCEvent_Message *message = cmd->replyData;

	if (!eq(cmd->command, "pivo")) return;
	
	int zbyva_piv = (time(NULL) - pivo->posledni_pivo) / 60 / pivo->minut_na_pivo;
	if (zbyva_piv > pivo->max_piv) {
		zbyva_piv = 6;
		pivo->posledni_pivo = time(NULL) - 60 * pivo->minut_na_pivo * pivo->max_piv;
	}

	printError(PLUG_NAME, "ted = %ld, posledni pivo = %ld, zbyva piv = %d", time(NULL), pivo->posledni_pivo, zbyva_piv);

	if (zbyva_piv > 0) {
		zbyva_piv--;

		if (eq(cmd->params, "")) {
			irclib_message(message->sender, message->channel, "Pivo pro %s:", message->address->nick);
		} else {
			irclib_message(message->sender, message->channel, "Pivo pro %s:", cmd->params);
		}

		// Send beer
		irclib_message(message->sender, message->channel, " *** \x03");
		irclib_message(message->sender, message->channel, "C\x03" "1,8|||\x03 ");
		irclib_message(message->sender, message->channel, " \x03" "1,8---\x03 ");

		if (zbyva_piv >= 5) {
			irclib_message(message->sender, message->channel, "Zbyva %d piv.",
				zbyva_piv);
		} else if (zbyva_piv >= 2) {
			irclib_message(message->sender, message->channel, "Zbyvaji %d piva.",
				zbyva_piv);
		} else if (zbyva_piv == 1) {
			irclib_message(message->sender, message->channel, "Zbyva %d pivo.",
				zbyva_piv);
		} else {
			irclib_message(message->sender, message->channel, "Zbyva %d piv.",
				zbyva_piv);
		}

		pivo->posledni_pivo += pivo->minut_na_pivo * 60;
	} else {
		irclib_message(message->sender, message->channel, "%s: Pivo doslo :(", message->address->nick);
	}
}

void PluginInit(PluginInfo *p) {
	pivo_data *plugData = malloc(sizeof(pivo_data));

	plugData->minut_na_pivo = 10;
	plugData->max_piv = 6;
	plugData->posledni_pivo = time(NULL) - 60 * plugData->minut_na_pivo * plugData->max_piv;

	plugData->onpivo = events_addEventListener(p->events, "oncommand", pivo_command, plugData);

	p->customData = plugData;
}

void PluginDone(PluginInfo *p) {
	pivo_data *plugData = (pivo_data *)p->customData;

	events_removeEventListener(plugData->onpivo);

	free(plugData);
}



