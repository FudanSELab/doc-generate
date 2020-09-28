from flask import Flask, request, jsonify
from flask_cors import CORS
from sekg.ir.doc.wrapper import MultiFieldDocumentCollection
from sekg.graph.exporter.graph_data import GraphData, NodeInfo

from project.knowledge_service import KnowledgeService
from project.doc_service import DocService
from project.json_service import JsonService
from project.utils.path_util import PathUtil
from pathlib import Path
import definitions
import json

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

pro_name = "jabref"
doc_dir = PathUtil.doc(pro_name=pro_name, version="v3.3")
graph_data_path = PathUtil.graph_data(pro_name=pro_name, version="v3.10")
graph_data: GraphData = GraphData.load(graph_data_path)
doc_collection: MultiFieldDocumentCollection = MultiFieldDocumentCollection.load(doc_dir)
simple_qualified_name_map_path = Path(definitions.ROOT_DIR) / "output" / "simple_qualified_name_map.json"

knowledge_service = KnowledgeService(doc_collection, graph_data)
doc_service = DocService()
json_service = JsonService()
with open(simple_qualified_name_map_path, 'r') as f:
    json_str = f.read()
simple_qualified_name_map = json.loads(json_str)
print("load complete")


@app.route('/')
def hello():
    return 'connect success'


# search doc info according to method name
@app.route('/get_doc/', methods=["GET", "POST"])
def doc_info():
    if "qualified_name" not in request.json:
        return "qualified name need"
    qualified_name = test_api(request.json['qualified_name'])
    node = graph_data.find_one_node_by_property(property_name="qualified_name", property_value=qualified_name)
    result = doc_service.get_doc_info(node['id'])
    return jsonify(result)


@app.route('/api_knowledge/', methods=["POST", "GET"])
def api_knowledge():
    if "qualified_name" not in request.json:
        return "qualified_name need"
    qualified_name = test_api(request.json['qualified_name'])
    result = knowledge_service.get_knowledge(qualified_name)
    return jsonify(result)


@app.route('/api_structure/', methods=["POST", "GET"])
def api_structure():
    if "qualified_name" not in request.json:
        return "qualified_name need"
    qualified_name = test_api(request.json['qualified_name'])
    result = knowledge_service.api_base_structure(qualified_name)
    return jsonify(result)


@app.route('/method_structure/', methods=["POST", "GET"])
def method_structure():
    if "qualified_name" not in request.json:
        return "qualified_name need"
    qualified_name = test_api(request.json['qualified_name'])
    api_id = knowledge_service.get_api_id_by_name(qualified_name)
    result = knowledge_service.get_api_methods(api_id, False)
    return jsonify(result)


# return top5 key methods of specific class
@app.route('/key_methods/', methods=["POST", "GET"])
def key_methods():
    if "qualified_name" not in request.json:
        return "qualified_name need"
    qualified_name = test_api(request.json['qualified_name'])
    res = knowledge_service.get_key_methods(qualified_name)
    return jsonify(res)


@app.route('/terminology/', methods=["POST", "GET"])
def api_terminologies():
    if "qualified_name" not in request.json:
        return "qualified_name need"
    qualified_name = test_api(request.json['qualified_name'])
    terminology_list = knowledge_service.get_api_terminologies(qualified_name)
    return jsonify(terminology_list)


# return sample code of specific class/method
@app.route('/sample_code/', methods=['POST', 'GET'])
def sample_code():
    if 'qualified_name' not in request.json:
        return 'qualified name need'
    qualified_name = test_api(request.json['qualified_name'])
    api_id = knowledge_service.get_api_id_by_name(qualified_name)
    if api_id is -1:
        return 'wrong qualified name'
    sample_code = doc_service.get_sample_code(api_id)
    if sample_code is None:
        return "no sample code"
    else:
        return sample_code


# return result which api as parameter and returen value
@app.route('/parameter_return_value/', methods=['POST', 'GET'])
def parameter_return_value():
    if 'qualified_name' not in request.json:
        return 'qualified name need'
    qualified_name = test_api(request.json['qualified_name'])
    as_parameter_list = json_service.api_as_parameter(qualified_name)
    as_return_value_list = json_service.api_as_return_value(qualified_name)

    parameter_result = list()
    for i in as_parameter_list:
        info = dict()
        node: NodeInfo = graph_data.find_one_node_by_property_value_starts_with(property_name="qualified_name",
                                                                                property_value_starter=i[:i.rfind("(")])
        info['qualified_name'] = i
        if node is None:
            info['sample_code'] = "No sample code available."
        else:
            info['sample_code'] = knowledge_service.get_one_sample_code(node['id'])
        parameter_result.append(info)

    return_value_result = list()
    for i in as_return_value_list:
        node: NodeInfo = graph_data.find_one_node_by_property_value_starts_with(property_name="qualified_name",
                                                                                property_value_starter=i[:i.rfind("(")])
        info = dict()
        info['qualified_name'] = i
        if node is None:
            info['sample_code'] = "No sample code available."
        else:
            info['sample_code'] = knowledge_service.get_one_sample_code(node['id'])
        return_value_result.append(info)
    result = dict()
    result['parameter'] = parameter_result
    result['return_value'] = return_value_result
    return jsonify(result)


# return the constructor of the class
@app.route('/constructor/', methods=['POST', 'GET'])
def get_constructor():
    if 'qualified_name' not in request.json:
        return 'qualified name need'
    qualified_name = test_api(request.json['qualified_name'])
    res = knowledge_service.get_constructor(qualified_name)
    return jsonify(res)


# return related api
@app.route('/related_api/', methods=['POST'])
def get_related_api():
    if 'qualified_name' not in request.json:
        return 'qualified name need'
    qualified_name = test_api(request.json['qualified_name'])
    res = knowledge_service.get_related_api(qualified_name)
    return jsonify(res)


def test_api(qualified_name):
    if qualified_name in simple_qualified_name_map:
        return simple_qualified_name_map[qualified_name]
    else:
        return "Do Not Find API"


if __name__ == '__main__':
    app.run()
