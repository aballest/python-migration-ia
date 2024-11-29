import os
import json
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key = 'AZURE_OPENAI_API_KEY',
    api_version = '2024-08-01-preview',
    azure_endpoint = 'AZURE_OPENAI_ENDPOINT'
)

def call_openai(messages):
    response = client.chat.completions.create(
        model = "AZURE_OPENAI_DEPLOYMENT_NAME",
        messages = messages,
        temperature = 0.7,
        max_tokens = 16384
    )

    print(f"Response done")

    return response.choices[0].message.content

def read_file(file_name):

    with open(file_name, 'r') as f:
        file_content = f.read()

        return file_content
  
def generate_message(prompt, code, input_example="", output_example=""):

    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": code}
    ]

    if input_example and output_example:
        messages.insert(1, {"role": "user", "content": input_example})
        messages.insert(2, {"role": "assistant", "content": output_example})

    return messages

def execute_entity_migration(file_name, destination_path):

    # Aquí establecemos el prompt
    prompt = """
    Eres un desarrollador experto en migraciones entre SpringMVC y SpringBoot 3 con arquitectura hexagonal.\n
    Tienes que transformar la entidad que viene de entrada, en código para una aplicación SpringBoot 3 teniendo en cuenta:\n
    - Tienes que reducir el boirlerplate con Lombok
    - Tienes que generar a partir de la entidad el DTO que se utilizará posteriormente en los controladores y servicios, con anotaciones válidas para OAS 3 y springdoc.
    - Tienes que generar el mapper de mapstruct para transformaciones entre entidad y dto
    Tienes que devolver el código transformado en formato JSON con cuatro campos:\n
    Campo model: Contendrá únicamente el código de la entidad migrada
    Campo dto: Contendrá únicamente el código del DTO generado
    Campo mapper: Contendrá únicamnte el código del Mapper generado
    Campo base_filename: Contendrá el nombre de la entidad, para poder nombrar posteriormente todos los ficheros
    """

    # Aquí leemos el ejemplo/s de entrada y salida
    input_example = read_file('code_examples/backend/entity_input.txt')
    output_example = read_file('code_examples/backend/entity_output.txt')

    # Aquí leemos el contenido del fichero del código fuente origen
    code = read_file(file_name)

    # Generamos los mensajes
    messages = generate_message(prompt, code, input_example, output_example)

    response = call_openai(messages)
    clean_response = response.replace("```json", "").replace("```", "")
    response_json = json.loads(clean_response, strict=False)

    # El response será un json
    filecontent_model = response_json['model']
    filecontent_dto = response_json['dto']
    filecontent_mapper = response_json['mapper']
    filename_base = response_json['base_filename']

    if not destination_path.endswith(os.sep):
        destination_path += os.sep
    
    destination_filename_model = destination_path + "/src/main/java/es/aballest/football/domain/model/" + filename_base + ".java"
    destination_filename_dto = destination_path + "/src/main/java/es/aballest/football/application/dto/" + filename_base + "Dto.java" 
    destination_filename_mapper = destination_path + "/src/main/java/es/aballest/football/application/dto/" + filename_base + "Mapper.java"

    with open(destination_filename_model, 'w') as f:
        f.write(filecontent_model)
    with open(destination_filename_dto, 'w') as f:
        f.write(filecontent_dto)
    with open(destination_filename_mapper, 'w') as f:
        f.write(filecontent_mapper)

def execute_dao_migration(file_name, destination_path):
    # Aquí establecemos el prompt
    prompt = """
    Eres un desarrollador experto en migraciones entre SpringMVC y SpringBoot 3 con arquitectura hexagonal.\n
    Tienes que transformar la implementación del DAO que viene de entrada, en un repositorio JPA para una aplicación SpringBoot 3 teniendo en cuenta:\n
    - Tienes que reducir el boirlerplate con Lombok. Puedes utilizar las anotaciones que consideres de lombok
    - Las prioridades en orden son:
     -- Utilizar los métodos de JPARepository si se adaptan a los métodos de entrada
     -- Utilizar DerivedNamedQuery si hay consultas específicas y se pueden realizar por éste método
     -- Utilizar las anotaciones @Query con JQPL
     -- Utilizar la anotación @Query con nativeQuery teniendo en cuenta que la base de datos es MySQL
    Tienes que devolver el código transformado en formato JSON con dos campos:\n
    Campo repository: Contendrá únicamente el código del DAO migrado
    Campo base_filename: Contendrá el nombre base de la entidad, para poder nombrar posteriormente todos los ficheros
    """

    # Aquí leemos el ejemplo/s de entrada y salida
    input_example = read_file('code_examples/backend/dao_input.txt')
    output_example = read_file('code_examples/backend/dao_output.txt')

    # Aquí leemos el contenido del fichero del código fuente origen
    code = read_file(file_name)

    # Generamos los mensajes
    messages = generate_message(prompt, code, input_example, output_example)

    response = call_openai(messages)
    clean_response = response.replace("```json", "").replace("```", "")
    response_json = json.loads(clean_response, strict=False)

    # El response será un json
    filecontent_repository = response_json['repository']
    filename_base = response_json['base_filename']

    if not destination_path.endswith(os.sep):
        destination_path += os.sep
    
    destination_filename_repository = destination_path + "/src/main/java/es/aballest/football/infrastructure/repository/" + filename_base + "Repository.java"

    with open(destination_filename_repository, 'w') as f:
        f.write(filecontent_repository)

def execute_service_controller_migration(file_name_service, file_name_controller, destination_path):
    # Aquí establecemos el prompt
    prompt = """
    Eres un desarrollador experto en migraciones entre SpringMVC y SpringBoot 3 con arquitectura hexagonal.\n
    Recibes como entrada un json con dos campos:\n
    - Campo service: Con la implementación de un servicio de SpringMVC
    - Campo controller: Con la implementación de un controlador de Spring MVC
    Tu objetivo es convertir estas especificaciones para servicios RESTFul de SpringBoot 3.
    Tienes que transformar la implementación del servicio que viene de entrada, en un servicio para una aplicación SpringBoot 3 teniendo en cuenta:\n
    - Tienes que reducir el boirlerplate con Lombok. Puedes utilizar las anotaciones que consideres de lombok\n
    - Tienes que utilizar DTO para la entrada y salida de los métodos\n
    - Tienes que utilizar repository JPA en lugar de DAO. Ya se dispone del repository JPA creado.\n
    - Las transformaciones entre entidad y DTO se tienen que realizar mediante MapStruct. Ya se dispone de una clase mapper para ello.\n
    También tienes que transformar la implementación del controller MVC que viene de entrada, a un RestController de SpringBoot 3 teniendo en cuenta:\n
    - Todos los métodos públicos del servicio deben estar expuestos como servicios REST en el controller
    - Se necesita que se genere las anotaciones necesarias para la documentación de Swagger utilizando OAS 3 y Springdoc, lo más detalladas posible
    - Tienes que reducir el boilerplate con Lombok. Puedes utilizar las anotaciones que consideres de Lombok\n
    - Si hay métodos en el controller que no son necesarios mantener (que son únicamente para mostrar vistas), no los transformes y omítelos
    Tienes que devolver el código transformado en formato JSON con cuatro campos:\n
    Campo service_impl: Contendrá únicamente el código de la implementación del servicio transformado
    Campo service_interface: Contendrá únicamente el código necesario para la especificación de la interfaz del servicio
    Campo controller: Contendrá únicamente el código necesario para la implementación del controller
    Campo base_filename: Contendrá el nombre base de la entidad, para poder nombrar posteriormente todos los ficheros
    """

    # Aquí leemos el ejemplo/s de entrada y salida
    input_example = read_file('code_examples/backend/service_controller_input.txt')
    output_example = read_file('code_examples/backend/service_controller_output.txt')

    # Aquí leemos el contenido del fichero del código fuente origen
    code_service = read_file(file_name_service)
    code_controller = read_file(file_name_controller)

    # Con ambos, generamos el json de entrada
    entry_data = {
        "service" : code_service,
        "controller" : code_controller
    }

    code = json.dumps(entry_data, indent=4)

    # Generamos los mensajes
    messages = generate_message(prompt, code, input_example, output_example)

    response = call_openai(messages)
    clean_response = response.replace("```json", "").replace("```", "")
    response_json = json.loads(clean_response, strict=False)

    # El response será un json
    filecontent_service_impl = response_json['service_impl']
    filecontent_service_interface = response_json['service_interface']
    filecontent_controller = response_json['controller']
    filename_base = response_json['base_filename']

    if not destination_path.endswith(os.sep):
        destination_path += os.sep
    
    destination_filename_service_impl = destination_path + "/src/main/java/es/aballest/football/application/service/impl/" + filename_base + "ServiceImpl.java"
    destination_filename_service_interface = destination_path + "/src/main/java/es/aballest/football/application/service/" + filename_base + "Service.java"
    destination_filename_controller = destination_path + "/src/main/java/es/aballest/football/infrastructure/webservice/" + filename_base + "Controller.java"

    with open(destination_filename_service_impl, 'w') as f:
        f.write(filecontent_service_impl)
    with open(destination_filename_service_interface, 'w') as f:
        f.write(filecontent_service_interface)
    with open(destination_filename_controller, 'w') as f:
        f.write(filecontent_controller)

def main(): 
    while True:
        print("\nOpciones disponibles:")
        print("1. Migración simple")
        print("2. Salir")

        # Preguntar al usuario la opción deseada
        opcion = input("\nElige una opción: (1-2):")

        if opcion == '1':
            file_name_entity = input("Indica la ruta y nombre de la entidad a migrar: ")
            file_name_dao = input("Indica la ruta y nombre del DAO a migrar: ")
            file_name_service = input("Indica la ruta y nombre del servicio a migrar: ")
            file_name_controller = input("Indica la ruta y nombre del controller a migrar: ")
            destination_path = input("Indica la ruta base del proyecto destino: ")

            if file_name_entity:
                execute_entity_migration(file_name_entity, destination_path)
            
            if file_name_dao:
                execute_dao_migration(file_name_dao, destination_path)

            if file_name_service and file_name_controller:
                execute_service_controller_migration(file_name_service, file_name_controller, destination_path)


        elif opcion == '2':
            print("Gracias por usar el programa. ¡Hasta luego!")
            break
        else:
            print("Opción no válida, por favor elige entre 1 y 3")
        
if __name__ == "__main__":
    main()
