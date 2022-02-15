import bokeh.application
import bokeh.application.handlers.function
import bokeh.server.server
import json
import logging

import app.config
import app.handler
import app.utils


logger = logging.getLogger(__name__)


def main():
    app.utils.init_logging()
    conf = app.config.build_config()
    # Logging supports only old style formatting
    logger.debug(
        "Application config:\n %s",
        json.dumps(conf, ensure_ascii=False, indent=4),
    )
    handler = app.handler.RevealAppHandler(conf["handler"])
    application = bokeh.application.Application(
        bokeh.application.handlers.function.FunctionHandler(handler)
    )
    server_ = bokeh.server.server.Server(
        applications={conf["server"]["app_route"]: application},
        allow_websocket_origin=conf["server"]["websocket_origin"],
    )
    server_.start()
    server_.io_loop.start()


if __name__ == "__main__":
    main()
