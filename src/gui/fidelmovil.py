// App.js
import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import SQLite from 'react-native-sqlite-storage';
import {
  SafeAreaView,
  View,
  Text,
  TouchableOpacity,
  FlatList,
  TextInput,
  StyleSheet,
  Modal,
  ScrollView,
  Alert,
} from 'react-native';

// Initialize SQLite database
const db = SQLite.openDatabase(
  { name: 'db_psicologia_clinic.db', location: 'default' },
  () => console.log('Database connected'),
  error => console.log('Database error', error)
);

const Stack = createNativeStackNavigator();

// Main App Component
const App = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="PatientList" component={PatientListScreen} options={{ title: 'Pacientes' }} />
        <Stack.Screen name="PatientDetail" component={PatientDetailScreen} options={{ title: 'Detalles' }} />
        <Stack.Screen name="ThoughtRecord" component={ThoughtRecordScreen} options={{ title: 'Registro' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

// Patient List Screen
const PatientListScreen = ({ navigation }) => {
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = () => {
    db.transaction(tx => {
      tx.executeSql(
        'SELECT * FROM pacientes ORDER BY codigo',
        [],
        (_, { rows: { _array } }) => setPatients(_array),
        error => console.log('Error loading patients:', error)
      );
    });
  };

  const renderPatientItem = ({ item }) => (
    <TouchableOpacity
      style={styles.patientItem}
      onPress={() => navigation.navigate('PatientDetail', { patientId: item.id, code: item.codigo })}
    >
      <Text style={styles.patientCode}>{item.codigo}</Text>
      <Text style={styles.patientName}>{item.nombre}</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={patients}
        renderItem={renderPatientItem}
        keyExtractor={item => item.id.toString()}
        initialNumToRender={10}
        maxToRenderPerBatch={10}
        windowSize={5}
      />
    </SafeAreaView>
  );
};

// Patient Detail Screen
const PatientDetailScreen = ({ route, navigation }) => {
  const [thoughts, setThoughts] = useState([]);
  const { code } = route.params;

  useEffect(() => {
    loadThoughts();
  }, []);

  const loadThoughts = () => {
    db.transaction(tx => {
      tx.executeSql(
        'SELECT * FROM pensamientos WHERE codigo LIKE ? ORDER BY codigo',
        [`${code}%`],
        (_, { rows: { _array } }) => setThoughts(_array),
        error => console.log('Error loading thoughts:', error)
      );
    });
  };

  const renderThoughtItem = ({ item }) => (
    <TouchableOpacity
      style={styles.thoughtItem}
      onPress={() => navigation.navigate('ThoughtRecord', { thoughtId: item.id, code: item.codigo })}
    >
      <Text style={styles.thoughtCode}>{item.codigo}</Text>
      <Text style={styles.thoughtText} numberOfLines={2}>{item.pensamiento}</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={thoughts}
        renderItem={renderThoughtItem}
        keyExtractor={item => item.id.toString()}
        initialNumToRender={10}
        maxToRenderPerBatch={10}
        windowSize={5}
      />
    </SafeAreaView>
  );
};

// Thought Record Screen
const ThoughtRecordScreen = ({ route }) => {
  const [dimensions, setDimensions] = useState({
    cantidad: 0,
    duracion: '',
    intensidad: 0
  });
  const [showModal, setShowModal] = useState(false);
  const { thoughtId, code } = route.params;

  const saveDimension = () => {
    if (dimensions.duracion && (parseInt(dimensions.duracion) < 0 || parseInt(dimensions.duracion) > 60)) {
      Alert.alert('Error', 'La duración debe estar entre 0 y 60 minutos');
      return;
    }

    db.transaction(tx => {
      tx.executeSql(
        `INSERT INTO dimensiones (pensamiento_id, fecha, cantidad, duracion, intensidad) 
         VALUES (?, date('now'), ?, ?, ?)`,
        [thoughtId, dimensions.cantidad, dimensions.duracion || null, dimensions.intensidad],
        () => {
          Alert.alert('Éxito', 'Dimensión guardada correctamente');
          setDimensions({ cantidad: 0, duracion: '', intensidad: 0 });
        },
        error => console.log('Error saving dimension:', error)
      );
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.recordContainer}>
          <Text style={styles.thoughtCode}>{code}</Text>
          
          <View style={styles.dimensionControl}>
            <Text>Cantidad:</Text>
            <View style={styles.counterContainer}>
              <TouchableOpacity
                style={styles.counterButton}
                onPress={() => setDimensions(prev => ({ ...prev, cantidad: Math.max(0, prev.cantidad - 1) }))}
              >
                <Text style={styles.buttonText}>-</Text>
              </TouchableOpacity>
              <Text style={styles.counterValue}>{dimensions.cantidad}</Text>
              <TouchableOpacity
                style={styles.counterButton}
                onPress={() => setDimensions(prev => ({ ...prev, cantidad: prev.cantidad + 1 }))}
              >
                <Text style={styles.buttonText}>+</Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.dimensionControl}>
            <Text>Duración (min):</Text>
            <TextInput
              style={styles.input}
              value={dimensions.duracion}
              onChangeText={text => {
                if (text === '' || (/^\d+$/.test(text) && parseInt(text) <= 60)) {
                  setDimensions(prev => ({ ...prev, duracion: text }));
                }
              }}
              keyboardType="numeric"
              maxLength={2}
            />
          </View>

          <View style={styles.dimensionControl}>
            <Text>Intensidad (0-10):</Text>
            <TextInput
              style={styles.input}
              value={dimensions.intensidad.toString()}
              onChangeText={text => {
                const value = parseInt(text);
                if (text === '' || (value >= 0 && value <= 10)) {
                  setDimensions(prev => ({ ...prev, intensidad: value || 0 }));
                }
              }}
              keyboardType="numeric"
              maxLength={2}
            />
          </View>

          <TouchableOpacity style={styles.saveButton} onPress={saveDimension}>
            <Text style={styles.saveButtonText}>Guardar</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.historyButton} onPress={() => setShowModal(true)}>
            <Text style={styles.historyButtonText}>Ver Historial</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      <Modal
        visible={showModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalView}>
          <Text style={styles.modalTitle}>Historial de Dimensiones</Text>
          {/* Aquí iría la lista de dimensiones previas */}
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => setShowModal(false)}
          >
            <Text style={styles.closeButtonText}>Cerrar</Text>
          </TouchableOpacity>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  patientItem: {
    backgroundColor: '#fff',
    padding: 15,
    marginVertical: 4,
    marginHorizontal: 8,
    borderRadius: 8,
    elevation: 2,
  },
  patientCode: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  patientName: {
    fontSize: 14,
    color: '#666',
  },
  thoughtItem: {
    backgroundColor: '#fff',
    padding: 15,
    marginVertical: 4,
    marginHorizontal: 8,
    borderRadius: 8,
    elevation: 2,
  },
  thoughtCode: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
    color: '#333',
  },
  thoughtText: {
    fontSize: 14,
    color: '#666',
  },
  recordContainer: {
    padding: 16,
  },
  dimensionControl: {
    marginVertical: 12,
  },
  counterContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  counterButton: {
    backgroundColor: '#007AFF',
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  counterValue: {
    marginHorizontal: 16,
    fontSize: 18,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 8,
    marginTop: 8,
    fontSize: 16,
  },
  saveButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 24,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  historyButton: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  historyButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalView: {
    flex: 1,
    marginTop: 60,
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  closeButton: {
    backgroundColor: '#ff3b30',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 24,
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default App;