const mongoose = require('mongoose')
const Schema = mongoose.Schema
mongoose.connect('mongodb://localhost/research_paper')
const paperSchema = new Schema({
  link: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  authors: {
    type: Array,
    required: true
  },
  institutes: {
    type: Array,
    required: true
  },
  DOI: {
    type: String,
    required: true
  },
  abstract: {
    type: String,
    required: true
  },
  date: {
    type: Object,
    required: true
  },
  areas: {
    type: Array,
    required: true
  },
  publication: {
    type: String,
    required: true
  },
  keywords: {
    type: Array
  }
})
const Paper = mongoose.model('Paper', paperSchema)

module.exports = Paper
