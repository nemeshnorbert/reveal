import bokeh.io
import logging
import json

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
    handler(bokeh.io.curdoc())


main()
