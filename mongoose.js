const mongoose = require('mongoose')
const Schema = mongoose.Schema
const url_local = 'mongodb://127.0.0.1/research_paper'
// const url_atlas = 'mongodb+srv://myoffice:SB0rLRpBmVj6Lcf0@cluster0.lyx5kly.mongodb.net/research_paper?retryWrites=true&w=majority'
const url_atlas =
  'mongodb+srv://zhutiannian:ZWYYJFztn212324@cluster0.lyx5kly.mongodb.net/research_paper?retryWrites=true&w=majority'
mongoose.connect(url_atlas)
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
  },
  topo_label: {
    type: Number
  }
})
const Paper = mongoose.model('Paper', paperSchema)

module.exports = Paper
