import json
import logging
import re

import pyjson5x

re_extra_data_message = re.compile(r"^Extra data .+? near (\d+)$")
re_error_position = re.compile(r"near (\d+)")
re_open_brace = re.compile(r"[\[{]")


class JsonNotFound(Exception):
    "Json format not found"


def parse(maybe_json, pydantic_model=None):
    json_objects = []
    while (index := re_open_brace.search(maybe_json)) is not None:
        index = index.span()[0]
        maybe_json = maybe_json[index:]
        try:
            json_objects.append(pyjson5x.decode(maybe_json))
            break
        except pyjson5x.Json5ExtraData as e:
            logging.debug(
                "There are other strings that are not JSON."
                " Re-explore for the trailing string."
            )
            match = re_extra_data_message.fullmatch(e.message)
            json_objects.append(e.result)
            maybe_json = maybe_json[int(match.group(1)) :]
        except pyjson5x.Json5DecoderException as e:
            logging.debug(
                f"JSON parse failed. {e.message}"
            )
            match = re_error_position.search(e.message)
            index = int(match.group(1))
            maybe_json = maybe_json[index:]

    if not json_objects:
        raise JsonNotFound

    if pydantic_model is None:
        return sorted(json_objects, key=lambda x: len(json.dumps(x)))[-1]
    else:
        import pydantic

        model = pydantic.main.create_model(
            "Temp",
            __root__=(pydantic_model, ...),
        )
        for json_object in json_objects:
            try:
                return model(__root__=json_object).dict(by_alias=True)["__root__"]
            except pydantic.ValidationError as e:
                logging.debug(f"{json_object} does not conform to the pydantic format.")
        raise JsonNotFound
